"""Defines the mockingbird class which handles requests."""

import logging
import queue
import random
import re
import time
from collections import namedtuple
from contextlib import AbstractContextManager
from queue import Queue
from threading import RLock, Thread
from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

import parse

from .beak_manager import BeakManager
from .config import Config
from .errors import MockingbirdError, MockingbirdUndefinedVar

# Match variables in strings such as "$(my_var). Capture variable name."
VAR_REGEX = re.compile(r'\$\(([\w\d]+)\)')
# Match sets of opening and closing curly braces.
BRACES_REGEX = re.compile(r'{+|}+')
# Match odd numbers of opening and closing curly braces.
# ODD_BRACES_REGEX = re.compile(r'(?<!{){(?>{{)*(?!{)|(?<!})}(?>}})*(?!})')


def _transform_formatter_syntax(string: str) -> Tuple[str, List[str]]:
    """Transform text from mockingbird syntax to the formatter syntax"""

    mb_vars = _parse_variables(string)
    esc_string = _escape_curly_braces(string)

    # Replace vars defined with "$(my_var)" syntax with replacement fields "{}"
    return (VAR_REGEX.sub(r'{}', esc_string), mb_vars)


def _transform_parse_syntax(string: str) -> Tuple[str, List[str]]:
    """Transform text from mockingbird syntax to the parse module syntax"""

    mb_vars = _parse_variables(string)
    esc_string = _escape_curly_braces(string)

    # Replace vars defined with "$(my_var)" syntax with vars defined as "{my_var}"
    return (VAR_REGEX.sub(r'{}', esc_string), mb_vars)


def _escape_curly_braces(string: str) -> str:
    """Escape curly braces by doubling the number of them."""

    return BRACES_REGEX.sub(r'\0\0', string)


def _parse_variables(string: str) -> List[str]:
    """Get a list of the variables in a string. List vars are in same order as in string."""

    return VAR_REGEX.findall(string)


class MockingbirdRequest:
    def __init__(self, raw_request: str, raw_response: Optional[str]) -> None:
        self._delay = 0
        self._raw_request = raw_request
        self._request_parser, self._req_vars = self._build_request(raw_request)

        self._raw_response = raw_response
        self._response, self._resp_vars = _transform_formatter_syntax(
            raw_response) if raw_response is not None else (None, [])

    @classmethod
    def _build_request(self, raw_request: str) -> Tuple['parse.Parse', List[str]]:
        req, req_vars = _transform_parse_syntax(raw_request)
        return (parse.compile(req), req_vars)

    @property
    def delay(self) -> int:
        return self._delay

    def parse(self, request: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse an incoming request.

        If the request doesn't match, return None.
        Otherwise return a dictionary of var names and values parsed from the request.
        """
        parsed_vals = self._request_parser.parse(request)

        if parsed_vals is None:
            return None

        if len(self._req_vars) != len(parsed_vals.fixed):
            # Not sure how this could happen, but make sure it doesn't
            raise MockingbirdError

        # Convert result to dictionary
        return {self._req_vars[i]: parsed_vals.fixed[i] for i in range(len(self._req_vars))}

    def build_response(self, mb_vars: Dict[str, 'MockingbirdVar']) -> Optional[str]:
        if self._response is None:
            return None

        vals = [mb_vars[resp_var].value for resp_var in self._resp_vars]
        return self._response.format(*vals)

class MockingbirdVar:
    def __init__(self, var_type: str, value: Any) -> None:
        self._var_type = var_type
        self._value = value
        self._lock = RLock()

    @property
    def value(self) -> Any:
        with self._lock:
            return self._value

    @value.setter
    def value(self, value: Any) -> None:
        with self._lock:
            self._value = value


class Mockingbird():
    """Class that holds the API for simulating the device."""

    # TYPE_MAP = {
    #     'str': ''
    # }  # type: Dict[str, str]


    def __init__(self, mb_name: str, log_q: Queue, config: Config) -> None:
        """Construct the mocking bird by internalizing the provided configs and requests."""

        LockedList = namedtuple('LockedList', 'lock, list')

        self._beak_manager = BeakManager(log_q, config)
        self._log = logging.getLogger(mb_name)

        # TODO. Allow configuring mode so user can choose between request delays stacking
        # or being immediate. Also whether output vars are determined immediatly when receiving
        # the request or are set when the delay is over.
        # self._mode

        self._mb_vars = {mb_var.name: MockingbirdVar(mb_var.value_type, mb_var.initial_value)
                         for mb_var in config.vars}  # type: Dict[str, MockingbirdVar]
        self._requests = {name: LockedList(RLock(), []) for name in self._beak_manager.interfaces}
        self._default_responses = {} # type: Dict[str, MockingbirdRequest]

        # Threadsafe queue for holding response events
        self._response_queue = queue.PriorityQueue()

        self._register_requests_thread = Thread(
            target=self._register_requests_loop)
        self._request_thread = Thread(target=self._request_loop)
        self._respond_thread = Thread(target=self._respond_loop)
        self._stop = False

    def __enter__(self) -> 'Mockingbird':
        self.start()
        return self

    def __exit__(self, ex: Optional[Type[BaseException]], val: Optional[BaseException],
                 trb: Optional[TracebackType]) -> None:
        self.stop()

    def start(self) -> None:
        self._beak_manager.start_all()
        self._stop = False
        self._register_requests_thread.start()
        self._request_thread.start()
        self._respond_thread.start()

    def stop(self) -> None:
        self._stop = True

        # Stop io loops before beak manager to avoid race conditions
        self._register_requests_thread.join()
        self._request_thread.join()
        self._respond_thread.join()

        self._beak_manager.stop_all()

    def _register_requests_loop(self) -> None:
        while not self._stop:
            try:
                req = self._beak_manager.register_request_queue.get(True, 0.1)
                self._register_request(*req)
            except queue.Empty:
                pass
            except:
                self._log.exception('Register requests thread crashed')
                raise

    def _register_request(self, interface: str, raw_req: Optional[str], raw_resp: Optional[str]) -> None:
        """Register a new set of request response pairs."""

        if raw_req and raw_resp is None:
            self._log.warning('Received invalid request to register with both request and response as none.')
            return


        if raw_req is None:
            # create default response
            self._default_responses[interface] = self._create_request('', raw_resp)
            self._log.info('Registered default response "%s" for "%s"', raw_resp, interface)
            return

        req = self._create_request(raw_req, raw_resp)

        with self._requests[interface].lock:
            self._requests[interface].list.append(req)

        self._log.info('Registered request "%s"', raw_req)

    def _create_request(self, raw_req: str, raw_resp: Optional[str]) -> MockingbirdRequest:
        """Create a request object."""

        self._verify_vars_defined(raw_req)

        if raw_resp is not None:
            self._verify_vars_defined(raw_resp)

        return MockingbirdRequest(raw_req, raw_resp)

    def _request_loop(self) -> None:
        while not self._stop:
            try:
                req = self._beak_manager.request_queue.get(True, 0.1)
                self._request(*req)
            except queue.Empty:
                pass
            except:
                self._log.exception('Request handler thread crashed')
                raise

    def _request(self, interface: str, key: Any, request: str) -> None:
        """Make request to the Mockingbird. Output the response."""

        self._log.info('Received request "%s" from %s',
                       request, interface)

        with self._requests[interface].lock:
            interface_requests = self._requests[interface].list

            # Shuffle interface reqs so that on average each request takes around
            # the same amount of time to find in the list. This keeps requests that
            # appear earlier in the list from always being completed faster than requests
            # found later in the list.
            random.shuffle(interface_requests)

            # Find the MockingbirdRequest that matches the incoming request and parse the request
            matching_request = None
            val_map = None
            for registered_request in interface_requests:
                val_map = registered_request.parse(request)

                if val_map is not None:  # Found a matching request, stop looking
                    matching_request = registered_request
                    break
            else:
                # Request didn't match any registered requests
                self._log.info(
                    'Request "%s" didn\'t match any registered requests.', request)

                matching_request = self._default_responses.get(interface, None)


            # Set the values parsed from the request
            if val_map is not None:
                for mb_var, val in val_map.items():
                    self._mb_vars[mb_var].value = val

            # Schedule the request to be responded to
            respond_time = time.time() + matching_request.delay
            self._response_queue.put(
                (respond_time, interface, key, matching_request))

    def _verify_vars_defined(self, raw_string: str) -> None:
        """Raises an exception if any variable in the string hasn't been defined."""

        for mb_var in _parse_variables(raw_string):
            if mb_var not in self._mb_vars:
                raise MockingbirdUndefinedVar(mb_var)

    def _respond_loop(self) -> None:
        while not self._stop:
            try:
                _, interface, key, match_req = self._response_queue.get(
                    True, 0.1)
                interface_queue = self._beak_manager.get_reponse_queue(
                    interface)
                response = match_req.build_response(self._mb_vars)
                interface_queue.put((key, response))
                self._log.info('Sending response "%s" to "%s"', response, interface)
            except queue.Empty:
                pass
            except:
                self._log.exception('Response handler thread crashed')
                raise
