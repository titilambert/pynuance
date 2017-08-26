"""Module defining Nuance Communications Services (NCS) Transaction"""
import asyncio


class NCSTransaction:
    """Class defining NCS transaction"""

    BEGIN_MESSAGE = 'query_begin'
    END_MESSAGE = 'query_end'
    ID_PROPERTY = 'transaction_id'

    def __init__(self, id_, session):
        self.id_ = id_
        self.session = session
        self.client = self.session.client
        self.response = {}

    @asyncio.coroutine
    def begin(self, **kwargs):
        """Send a 'query_begin' augmenting the payload with any additional kwargs,
        e.g. 'command', 'context_tag', 'language', etc.
        """
        payload = {
            'message': self.BEGIN_MESSAGE,
        }
        payload.update(kwargs)
        yield from self._send_json(payload)

    @asyncio.coroutine
    def send_parameter(self, name, type_, value):
        """Send a 'query_parameter' message.

        :param name: Corresponds to `parameter_name`
        :param type_: Corresponds to `parameter_type`
        :param value: The parameter itself. Should be a {key: value} dictionary
        """
        payload = {
            'message': 'query_parameter',
            'parameter_name': name,
            'parameter_type': type_,
        }
        payload.update(value)
        yield from self._send_json(payload)

    @asyncio.coroutine
    def end(self, wait=True, timeout=None):
        """Send a 'query_end' message and wait to receive an acknowledgement or
        disconnection message.

        :param wait: (bool) Wait for server-side confirmation before returning.
        :param timeout: (in seconds) How long you are willing to wait without
        receiving a payload.
        """
        yield from self._send_json({'message': self.END_MESSAGE})
        if wait:
            message = yield from self.wait_for_query_end(timeout)
            return message

    @asyncio.coroutine
    def _send_json(self, message):
        """Send a JSON payload using the original WS client.

        Injects the transaction ID in the payload, modifying the dictionary,
        so the transaction_id can be logged properly.
        """
        message.update({self.ID_PROPERTY: self.id_})
        return(yield from self.client.send_json(message))

    @asyncio.coroutine
    def wait_for_query_end(self, timeout=None, is_bytes=False):
        """Wait for "end" query meaning end of communication """
        while True:
            if not is_bytes:
                message = yield from self.client.receive_json(timeout=timeout)
                if message['message'] == 'query_response':
                    self.response = message
                elif message['message'] in ('query_end', 'disconnect'):
                    return message
            else:
                message = yield from self.client.receive_bytes(timeout=timeout)
                return message


class NCSAudioTransfer(NCSTransaction):
    """Transaction used to stream audio bytes.

    Behaves similarly to other NCS transactions, but with different parameter
    names and some minor behavior differences.
    """

    BEGIN_MESSAGE = 'audio'
    END_MESSAGE = 'audio_end'
    ID_PROPERTY = 'audio_id'

    @property
    def info(self):
        """Payload should be sent in the AUDIO_INFO.

        Expected format is:

            {"audio_id": 123}
        """
        return {self.ID_PROPERTY: self.id_}

    @asyncio.coroutine
    def send_bytes(self, bytes_, *args, **kwargs):
        """Send audio data"""
        yield from self.client.send_bytes(bytes_, *args, **kwargs)
