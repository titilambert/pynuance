"""Module defining abstractWebsocket class"""

import asyncio
import base64
import binascii
import email
import hashlib
import hmac
import json
import os
import datetime
import urllib.parse

import aiohttp
try:
    from aiohttp import websocket
except ImportError:
    from aiohttp import _ws_impl as websocket


# This is a fixed string (constant), used in the Websockets protocol handshake
# in order to establish a conversation
WS_KEY = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


def connection_handshake(client):
    """Nuance connection handshake.

    Use for STT and NLU audio.
    """
    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'AUDIO_INFO',
        'parameter_type': 'audio',

        'audio_id': 456
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    client.send_message({
        'message': 'audio',
        'audio_id': 456,
    })


class AbstractWebsocketConnection(object):  # pylint: disable=R0801
    """WebSocket connection object to handle Nuance server communications"""
    MSG_JSON = 1
    MSG_AUDIO = 2

    def __init__(self, url, logger):
        self.url = url
        self.logger = logger
        self.connection = None
        self.response = None
        self.stream = None
        self.writer = None

    @asyncio.coroutine
    def connect(self, app_id, app_key, use_plaintext=True):
        """Connect to the websocket"""
        raise NotImplementedError

    @asyncio.coroutine
    def receive(self):
        """Handle server response"""
        wsmsg = yield from self.stream.read()
        if wsmsg.tp == 1:
            return (self.MSG_JSON, json.loads(wsmsg.data))

        return (self.MSG_AUDIO, wsmsg.data)

    def send_message(self, msg):
        """Send json message to the server"""
        self.logger.debug(msg)
        self.writer.send(json.dumps(msg))

    def send_audio(self, audio):
        """Send audio to the server"""
        self.writer.send(audio, binary=True)

    def close(self):
        """Close WebSocket connection"""
        self.writer.close()
        self.response.close()
        self.connection.close()

    @staticmethod
    def _handle_response_101(response):
        """handle response"""
        info = "%s %s\n" % (response.status, response.reason)
        for (key, val) in response.headers.items():
            info += '%s: %s\n' % (key, val)
        info += '\n%s' % (yield from response.read()).decode('utf-8')

        if response.status == 401:
            raise RuntimeError("Authorization failure:\n%s" % info)
        elif response.status >= 500 and response.status < 600:
            raise RuntimeError("Server error:\n%s" % info)
        elif response.headers.get('upgrade', '').lower() != 'websocket':
            raise ValueError("Handshake error - Invalid upgrade header")
        elif response.headers.get('connection', '').lower() != 'upgrade':
            raise ValueError("Handshake error - Invalid connection header")
        else:
            raise ValueError("Handshake error: Invalid response status:\n%s" % info)

    def _handshake(self, response, sec_key):
        """Websocket handshake"""
        # Using WS_KEY in handshake
        key = response.headers.get('sec-websocket-accept', '').encode()
        match = base64.b64encode(hashlib.sha1(sec_key + WS_KEY).digest())
        if key != match:
            raise ValueError("Handshake error - Invalid challenge response")

        # switch to websocket protocol
        self.connection = response.connection
        self.stream = self.connection.reader.set_parser(websocket.WebSocketParser)
        self.writer = websocket.WebSocketWriter(self.connection.writer)
        self.response = response


class BadWebsocketConnection(AbstractWebsocketConnection):
    """WebSocket connection object to handle Nuance server communications"""

    def __init__(self, url, logger):
        AbstractWebsocketConnection.__init__(self, url, logger)

    @asyncio.coroutine
    def connect(self, app_id, app_key, use_plaintext=True):
        """Connect to the server"""
        sec_key = base64.b64encode(os.urandom(16))

        params = {'app_id': app_id, 'algorithm': 'key', 'app_key': binascii.hexlify(app_key)}

        response = yield from aiohttp.request('get',
                                              self.url + '?' + urllib.parse.urlencode(params),
                                              headers={'UPGRADE': 'WebSocket',
                                                       'CONNECTION': 'Upgrade',
                                                       'SEC-WEBSOCKET-VERSION': '13',
                                                       'SEC-WEBSOCKET-KEY': sec_key.decode(),
                                                       })

        if response.status != 101:
            self._handle_response_101(response)

        self._handshake(response, sec_key)


class WebsocketConnection(AbstractWebsocketConnection):
    """Websocket client"""

    def __init__(self, url, logger):
        AbstractWebsocketConnection.__init__(self, url, logger)

    @asyncio.coroutine
    def connect(self, app_id, app_key, use_plaintext=True):
        """Connect to the websocket"""
        date = datetime.datetime.utcnow()
        sec_key = base64.b64encode(os.urandom(16))

        if use_plaintext:
            params = {
                'app_id': app_id,
                'algorithm': 'key',
                'app_key': binascii.hexlify(app_key),
            }
        else:
            datestr = date.replace(microsecond=0).isoformat()
            params = {
                'date': datestr,
                'app_id': app_id,
                'algorithm': 'HMAC-SHA-256',
                'signature': self.sign_credentials(datestr, app_key, app_id),
            }

        response = yield from aiohttp.request(
            'get', self.url + '?' + urllib.parse.urlencode(params),
            headers={
                'UPGRADE': 'WebSocket',
                'CONNECTION': 'Upgrade',
                'SEC-WEBSOCKET-VERSION': '13',
                'SEC-WEBSOCKET-KEY': sec_key.decode(),
            })

        if response.status == 401 and not use_plaintext:
            if 'Date' in response.headers:
                server_date = email.utils.parsedate_to_datetime(response.headers['Date'])
                if server_date.tzinfo is not None:
                    server_date = (server_date - server_date.utcoffset()).replace(tzinfo=None)
            else:
                server_date = yield from response.read()
                server_date = datetime.datetime.strptime(server_date[:19].decode('ascii'),
                                                         "%Y-%m-%dT%H:%M:%S")

            # Use delta on future requests
            date_delta = server_date - date

            print("Retrying authorization (delta=%s)" % date_delta)

            datestr = (date + date_delta).replace(microsecond=0).isoformat()
            params = {
                'date': datestr,
                'algorithm': 'HMAC-SHA-256',
                'app_id': app_id,
                'signature': self.sign_credentials(datestr, app_key, app_id),
            }

            response = yield from aiohttp.request('get',
                                                  self.url + '?' + urllib.parse.urlencode(params),
                                                  headers={'UPGRADE': 'WebSocket',
                                                           'CONNECTION': 'Upgrade',
                                                           'SEC-WEBSOCKET-VERSION': '13',
                                                           'SEC-WEBSOCKET-KEY': sec_key.decode(),
                                                           })

        if response.status != 101:
            self._handle_response_101(response)

        self._handshake(response, sec_key)

    @staticmethod
    def sign_credentials(datestr, app_key, app_id):
        """Handle credentials"""
        value = datestr.encode('ascii') + b' ' + app_id.encode('utf-8')
        return hmac.new(app_key, value, hashlib.sha256).hexdigest()
