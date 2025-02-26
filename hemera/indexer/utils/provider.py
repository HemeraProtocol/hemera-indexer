import json
import socket
from json import JSONDecodeError
from urllib.parse import urlparse

from web3 import HTTPProvider, IPCProvider
from web3._utils.http_session_manager import HTTPSessionManager
from web3._utils.threads import Timeout

DEFAULT_TIMEOUT = 60


def get_provider_from_uri(uri_string, timeout=DEFAULT_TIMEOUT, batch=False):
    uri = urlparse(uri_string)
    if uri.scheme == "file":
        if batch:
            return BatchIPCProvider(uri.path, timeout=timeout)
        else:
            return IPCProvider(uri.path, timeout=timeout)
    elif uri.scheme == "http" or uri.scheme == "https":
        request_kwargs = {"timeout": timeout}
        if batch:
            return BatchHTTPProvider(uri_string, request_kwargs=request_kwargs)
        else:
            return HTTPProvider(uri_string, request_kwargs=request_kwargs)
    else:
        raise ValueError("Unknown uri scheme {}".format(uri_string))


class BatchIPCProvider(IPCProvider):
    _socket = None

    def make_request(self, method=None, params=None):
        request = params.encode("utf-8")
        with self._lock, self._socket as sock:
            try:
                sock.sendall(request)
            except BrokenPipeError:
                # one extra attempt, then give up
                sock = self._socket.reset()
                sock.sendall(request)

            raw_response = b""
            with Timeout(self.timeout) as timeout:
                while True:
                    try:
                        raw_response += sock.recv(4096)
                    except socket.timeout:
                        timeout.sleep(0)
                        continue
                    if raw_response == b"":
                        timeout.sleep(0)
                    elif has_valid_json_rpc_ending(raw_response):
                        try:
                            response = json.loads(raw_response.decode("utf-8"))
                            timeout.sleep(0)
                        except JSONDecodeError:
                            continue
                        else:
                            return response
                    else:
                        timeout.sleep(0)
                        continue


class BatchHTTPProvider(HTTPProvider):
    http_manager = HTTPSessionManager(100, 5)

    def make_request(self, method=None, params=None):
        self.logger.debug("Making request HTTP. URI: %s, Request: %s", self.endpoint_uri, params)
        if isinstance(params, str):
            request_data = params.encode("utf-8")
        else:
            request_data = params
        raw_response = self.http_manager.make_post_request(self.endpoint_uri, request_data, **self.get_request_kwargs())
        try:
            response = self.decode_rpc_response(raw_response)
        except JSONDecodeError:
            self.logger.error("JSON decode error, params: %s, raw_response: %s", params, raw_response)
            raise
        self.logger.debug(
            "Getting response HTTP. URI: %s, " "Request: %s, Response: %s",
            self.endpoint_uri,
            params,
            response,
        )
        return response


def has_valid_json_rpc_ending(raw_response):
    for valid_ending in [b"}\n", b"]\n"]:
        if raw_response.endswith(valid_ending):
            return True
    else:
        return False
