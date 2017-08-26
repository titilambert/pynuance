"""Module defining Nuance Communications Services Session"""
import asyncio
import itertools

from pynuance.ncstransaction import NCSTransaction


class NCSSession:
    """NCS session object"""

    def __init__(self, client):
        self.id_ = None  # Assigned upon initial request
        self.client = client
        self._transaction_id_generator = itertools.count(start=1, step=1)
        self._audio_id_generator = itertools.count(start=1, step=1)

    @asyncio.coroutine
    def initiate(self, user_id, device_id, **kwargs):
        """Initiate the session"""
        payload = {
            'message': 'connect',
            'device_id': device_id,
            'user_id': user_id,
        }
        payload.update(kwargs)
        yield from self.client.send_json(payload)
        message = yield from self.client.receive_json()
        if message.get('message') != 'connected':
            raise RuntimeError('Invalid session connection message')

        self.id_ = message['session_id']

    @asyncio.coroutine
    def begin_transaction(self, *args, **kwargs):
        """Start a new transaction"""
        transaction_id = self.get_new_transaction_id()
        transaction = NCSTransaction(transaction_id, session=self)
        yield from transaction.begin(*args, **kwargs)
        return transaction

    def get_new_transaction_id(self):
        """Return the new transaction id"""
        return next(self._transaction_id_generator)

    def get_new_audio_id(self):
        """Return the new audio id"""
        return next(self._audio_id_generator)
