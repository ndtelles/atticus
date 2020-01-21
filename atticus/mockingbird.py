"""Defines the mockingbird class which handles requests."""

import logging
import queue
import random
import re
import time
from collections import namedtuple
from queue import Queue, PriorityQueue
from threading import RLock, Thread
from types import TracebackType
from typing import Any, Dict, List, Tuple, Type
from typing import Optional as Opt

import parse

from .beak_manager import BeakManager
from .config import Config
from .errors import MockingbirdError, MockingbirdUndefinedVar

# Match variables in strings such as "$(my_var). Capture variable name."
VAR_REGEX = re.compile(r'\$\(([\w\d]+)\)')
# Match sets of opening and closing curly braces.
BRACES_REGEX = re.compile(r'{+|}+')


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

    # Replace vars defined with "$(my_var)" syntax with "{}"
    return (VAR_REGEX.sub(r'{}', esc_string), mb_vars)


def _escape_curly_braces(string: str) -> str:
    """Escape curly braces by doubling the number of them."""

    return BRACES_REGEX.sub(r'\0\0', string)


def _parse_variables(string: str) -> List[str]:
    """Get list of vars in string. List vars are in same order as string."""

    return VAR_REGEX.findall(string)


class _Request:
    def __init__(self, raw_request: str, raw_response: Opt[str]) -> None:
        self._delay = 0
        self._raw_request = raw_request
        self._request_parser, self._req_vars = self._build_request(raw_request)

        self._raw_response = raw_response
        self._response, self._resp_vars = _transform_formatter_syntax(
            raw_response) if raw_response is not None else (None, [])

    @classmethod
    def _build_request(self, raw_req: str) -> Tuple['parse.Parse', List[str]]:
        req, req_vars = _transform_parse_syntax(raw_req)
        return (parse.compile(req), req_vars)

    @property
    def delay(self) -> int:
        return self._delay

    def parse(self, request: str) -> Opt[Dict[str, Any]]:
        """Attempt to parse an incoming request.

        If the request doesn't match, return None.
        Otherwise return dictionary of var names and values parsed from the
        request.
        """
        vals = self._request_parser.parse(request)
        mb_vars = self._req_vars

        if vals is None:
            return None

        if len(mb_vars) != len(vals.fixed):
            # Not sure how this could happen, but make sure it doesn't
            raise MockingbirdError

        # Convert result to dictionary
        return {mb_vars[i]: vals.fixed[i] for i in range(len(mb_vars))}

    def build_response(self, mb_vars: Dict[str, '_Var']) -> Opt[str]:
        if self._response is None:
            return None

        vals = [mb_vars[resp_var].value for resp_var in self._resp_vars]
        return self._response.format(*vals)


class _Var:
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

    def __init__(self, mb_name: str, log_q: Queue, config: Config) -> None:
        """Construct mockingbird."""

        LockedList = namedtuple('LockedList', 'lock, list')

        self._beak_manager = BeakManager(log_q, config)
        self._log = logging.getLogger(mb_name)

        # TODO. Allow configuring mode so user can choose between request
        # delays stacking or being immediate. Also whether output vars are
        # determined when receiving the request or are set when the delay is
        # over.

        self._mb_vars = {mb_var.name:
                         _Var(mb_var.value_type, mb_var.initial_value)
                         for mb_var in config.vars}  # type: Dict[str, _Var]
        self._requests = {name: LockedList(
            RLock(), []) for name in self._beak_manager.interfaces}
        self._default_responses = {}  # type: Dict[str, _Request]

        # Threadsafe queue for holding response events
        self._response_queue = PriorityQueue(
        )  # type: PriorityQueue[Tuple[float,str,Any,_Request]]

        self._register_requests_thread = Thread(
            target=self._register_requests_loop)
        self._request_thread = Thread(target=self._request_loop)
        self._respond_thread = Thread(target=self._respond_loop)
        self._stop = False

    def __enter__(self) -> 'Mockingbird':
        self.start()
        return self

    def __exit__(self, ex: Opt[Type[BaseException]], val: Opt[BaseException],
                 trb: Opt[TracebackType]) -> None:
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
            except Exception:
                self._log.exception('Register requests thread crashed')
                raise

    def _register_request(self, beak: str, raw_req: Opt[str], raw_resp: Opt[str]) -> None:
        """Register a new set of request response pairs."""

        if raw_req and raw_resp is None:
            self._log.warning('Received invalid register request.')
            return

        if raw_req is None:
            # create default response
            self._default_responses[beak] = self._create_request('', raw_resp)
            self._log.info(
                'Registered default response "%s" for "%s"', raw_resp, beak)
            return

        req = self._create_request(raw_req, raw_resp)

        with self._requests[beak].lock:
            self._requests[beak].list.append(req)

        self._log.info('Registered request "%s"', raw_req)

    def _create_request(self, raw_req: str, raw_resp: Opt[str]) -> _Request:
        """Create a request object."""

        self._verify_vars_defined(raw_req)

        if raw_resp is not None:
            self._verify_vars_defined(raw_resp)

        return _Request(raw_req, raw_resp)

    def _request_loop(self) -> None:
        while not self._stop:
            try:
                req = self._beak_manager.request_queue.get(True, 0.1)
                self._request(*req)
            except queue.Empty:
                pass
            except Exception:
                self._log.exception('Request handler thread crashed')
                raise

    def _request(self, beak: str, key: Any, req: str) -> None:
        """Make request to the Mockingbird. Output the response."""

        self._log.info('Received request "%s" from %s',
                       req, beak)

        with self._requests[beak].lock:
            beak_requests = self._requests[beak].list

            # Shuffle interface reqs so that on average each request takes
            # the same amount of time to find in the list. This keeps requests
            # that appear earlier in the list from always being completed
            # faster than requests found later in the list.
            random.shuffle(beak_requests)

            # Find the Request that matches the incoming request and parse it
            matching_request = None
            val_map = None
            for registered_request in beak_requests:
                val_map = registered_request.parse(req)

                if val_map is not None:  # Found a matching request
                    matching_request = registered_request
                    break
            else:
                # Request didn't match any registered requests
                self._log.info(
                    'Request "%s" didn\'t match any registered requests.', req)

                matching_request = self._default_responses.get(beak, None)

            # Set the values parsed from the request
            if val_map is not None:
                for mb_var, val in val_map.items():
                    self._mb_vars[mb_var].value = val

            # Schedule the request to be responded to
            respond_time = time.time() + matching_request.delay
            self._response_queue.put(
                (respond_time, beak, key, matching_request))

    def _verify_vars_defined(self, raw_string: str) -> None:
        """Raises exception if any variable in string hasn't been defined."""

        for mb_var in _parse_variables(raw_string):
            if mb_var not in self._mb_vars:
                raise MockingbirdUndefinedVar(mb_var)

    def _respond_loop(self) -> None:
        while not self._stop:
            try:
                _, beak, key, match_req = self._response_queue.get(True, 0.1)
                beak_queue = self._beak_manager.get_reponse_queue(beak)
                response = match_req.build_response(self._mb_vars)
                beak_queue.put((key, response))
                self._log.info('Sending response "%s" to "%s"', response, beak)
            except queue.Empty:
                pass
            except Exception:
                self._log.exception('Response handler thread crashed')
                raise
