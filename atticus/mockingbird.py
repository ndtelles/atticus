from typing import Dict


class MockingBird:
    """ Class that holds the API for simulating the device. """

    TERMINATORS = {
        'lf': "\n",
        'crlf': "\r\n",
        'none': ""
    }

    def __init__(self, requests: Dict[str, str] = {}, props: Dict[str, str] = {}) -> None:
        """ Construct the mocking bird by internalizing the provided configs and requests. """

        self.case_sensitive = props.get('case_sensitive', False)
        self.terminator = props.get('terminator', 'lf').lower()
        
        self.requests = {}
        self.register_requests(requests)
        
    def register_requests(self, new_reqs: Dict[str, str]) -> None:
        """ Register a new set of request response pairs. """

        self.requests.update(new_reqs)
    
    def request(self, reqs_str: str) -> str:
        """ Make request to the Mockingbird. Output the response. """

        if self.terminator == 'none':
            reqs = [reqs_str]
        else:
            reqs = reqs_str.split(MockingBird.TERMINATORS[self.terminator])
            
        data = ''
        for req in filter(None, reqs):
            if not self.case_sensitive:
                req = req.lower()
            data = self.requests.get(req, '')

        # Currently will only respond to last request!
        return data + MockingBird.TERMINATORS[self.terminator]
