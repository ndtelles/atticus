"""Defines the mockingbird class which handles requests."""

from typing import Dict, Optional


class Mockingbird:
    """Class that holds the API for simulating the device."""

    TERMINATORS = {
        'lf': "\n",
        'crlf': "\r\n",
        'none': ""
    }

    def __init__(self, requests: Optional[Dict[str, str]], props: Optional[Dict[str, str]]) -> None:
        """Construct the mocking bird by internalizing the provided configs and requests."""

        if props is None:
            props = {}

        self.case_sensitive = props.get('case_sensitive', False)
        self.terminator = props.get('terminator', 'lf').lower()

        self.requests: Dict[str, str] = {}
        self.register_requests(requests)

    def register_requests(self, new_reqs: Optional[Dict[str, str]]) -> None:
        """Register a new set of request response pairs."""

        if new_reqs is not None:
            self.requests.update(new_reqs)

    def request(self, reqs_str: str) -> str:
        """Make request to the Mockingbird. Output the response."""

        # @TODO: Check if this none check is necessary. If so, document why
        if self.terminator == 'none':
            reqs = [reqs_str]
        else:
            reqs = reqs_str.split(Mockingbird.TERMINATORS[self.terminator])

        data = ''
        for req in filter(None, reqs):
            if not self.case_sensitive:
                req = req.lower()
            data = self.requests.get(req, '')

        # Currently will only respond to last request!
        return data + Mockingbird.TERMINATORS[self.terminator]
