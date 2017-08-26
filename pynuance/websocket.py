"""Module defining abstractWebsocket class"""
import asyncio
import logging

import aiohttp
from aiohttp.client_exceptions import WSServerHandshakeError
from yarl import URL

from pynuance.ncssession import NCSSession


class NCSWebSocketClient:
    """Client for Nuance Cloud Services (NCS) WebSocket API

    For more info on the protocol:
    https://developer.nuance.com/mix/documentation/websockets/

    This client only supports one session + transaction at a time.
    """

    def __init__(self, url, app_id, app_key):
        self.url = URL(url)
        self.app_id = app_id
        self.app_key = app_key
        self._http_session = None
        self._ws_client = None
        self.logger = logging.getLogger("pynuance").getChild("websocket")

    @asyncio.coroutine
    def connect(self):
        """Connect to the NCS"""
        self._http_session = aiohttp.ClientSession()
        url = self.url.update_query(app_id=self.app_id, app_key=self.app_key,
                                    algorithm='key')
        try:
            self._ws_client = yield from self._http_session.ws_connect(url)
        except WSServerHandshakeError as ws_error:
            info = '%s %s\n' % (ws_error.code, ws_error.message)
            for (key, val) in ws_error.headers.items():
                info += '%s: %s\n' % (key, val)
            if ws_error.code == 401:
                raise RuntimeError('Authorization failure:\n%s' % info) from ws_error
            elif 500 <= ws_error.code < 600:
                raise RuntimeError('Server error:\n%s' % info) from ws_error
            else:
                raise ws_error

    @asyncio.coroutine
    def init_session(self, user_id, device_id, **kwargs):
        """Start a new session"""
        session = NCSSession(client=self)
        yield from session.initiate(user_id, device_id, **kwargs)
        return session

    @asyncio.coroutine
    def receive_json(self, *args, **kwargs):
        """Read json response"""
        message = yield from self._ws_client.receive_json(*args, **kwargs)
        self.logger.debug("Receive json: %s", message)
        return message

    @asyncio.coroutine
    def receive_bytes(self, *args, **kwargs):
        """Read raw response (audio data)"""
        message = yield from self._ws_client.receive_bytes(*args, **kwargs)
        self.logger.debug("Receive bytes")
        return message

    @asyncio.coroutine
    def receive(self, *args, **kwargs):
        """Read raw response (audio data)"""
        # TODO: delete me ???
        message = yield from self._ws_client.receive_bytes(*args, **kwargs)
        self.logger.debug("Receive bytes")
        return message

    @asyncio.coroutine
    def send_json(self, message, *args, **kwargs):
        """Send json data"""
        self.logger.debug("Send json: %s", message)
        yield from self._ws_client.send_json(message, *args, **kwargs)

    @asyncio.coroutine
    def send_bytes(self, bytes_, *args, **kwargs):
        """Send raw data (audio data)"""
        self.logger.debug("Send bytes")
        yield from self._ws_client.send_bytes(bytes_, *args, **kwargs)

    @asyncio.coroutine
    def close(self):
        """Close communication"""
        if self._ws_client is not None and not self._ws_client.closed:
            yield from self._ws_client.close()
        if self._http_session is not None and not self._http_session.closed:
            self._http_session.close()
