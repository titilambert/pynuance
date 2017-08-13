"""Provides Natural Language Understanding functions"""

import asyncio
import binascii
import logging

import aiohttp

from pynuance.websocket import WebsocketConnection, connection_handshake
from pynuance.libs.languages import NLU_LANGUAGES
from pynuance.libs.error import PyNuanceError
from pynuance.recorder import Recorder, listen_microphone


def understand_audio(app_id, app_key, context_tag, language, logger=None):
    """NLU audio wrapper"""
    # transform language
    if logger is None:
        logger = logging.getLogger("pynuance").getChild("nlu").getChild("audio")
    nlu_language = NLU_LANGUAGES.get(language)
    if nlu_language is None:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(NLU_LANGUAGES.keys())))

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    interpretations = {}
    with Recorder(loop=loop) as recorder:
        interpretations = loop.run_until_complete(_nlu_audio(
            loop,
            "https://ws.dev.nuance.com",
            app_id,
            binascii.unhexlify(app_key),
            context_tag,
            nlu_language,
            recorder=recorder,
            logger=logger,))
    # loop.close()
    if interpretations is False:
        # The user did not speak
        return {}

    return interpretations


@asyncio.coroutine
def _nlu_audio(loop, url, app_id, app_key, context_tag,  # pylint: disable=R0914
               language, recorder, logger):
    """Trying to understand audio"""
    # Websocket client
    client = WebsocketConnection(url, logger)
    yield from client.connect(app_id, app_key)

    # Init Nuance communication
    audio_type = 'audio/x-speex;mode=wb'
    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type
    })

    _, msg = yield from client.receive()

    # logger.debug(msg)  # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NDSP_ASR_APP_CMD',
        'language': language,
        'context_tag': context_tag,
    })

    connection_handshake(client)

    receivetask = asyncio.ensure_future(client.receive())
    audiotask = asyncio.ensure_future(recorder.dequeue())

    yield from listen_microphone(loop, client, recorder, audiotask, receivetask, logger)

    recorder.stop()

    logger.debug("Send last message to Mix")
    client.send_message({
        'message': 'audio_end',
        'audio_id': 456,
    })

    interpretation = {}
    while True:
        yield from asyncio.wait((receivetask,), loop=loop)
        try:
            _, msg = receivetask.result()
        except aiohttp.errors.ServerDisconnectedError:
            raise PyNuanceError("Error, check your context tag {} existence "
                                "in MIX".format(context_tag))
        logger.debug(msg)

        if msg['message'] == 'query_end':
            break
        else:
            interpretation = msg

        receivetask = asyncio.ensure_future(client.receive())

    client.close()
    return interpretation


def understand_text(app_id, app_key, context_tag, language, text, logger=None):
    """Nlu text wrapper"""
    if logger is None:
        logger = logging.getLogger("pynuance").getChild("nlu").getChild("text")
    # transform language
    nlu_language = NLU_LANGUAGES.get(language)
    if nlu_language is None:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(NLU_LANGUAGES.keys())))

    logger.debug("Text received: {}".format(text))
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # TODO: try/except
    interpretations = loop.run_until_complete(
        _nlu_text("https://ws.dev.nuance.com",
                  app_id,
                  binascii.unhexlify(app_key),
                  context_tag,
                  text,
                  nlu_language,
                  logger,
                  ))
    # loop.close()
    if interpretations is False:
        # The user did not speak
        return {}

    return interpretations


@asyncio.coroutine
def _nlu_text(url, app_id, app_key, context_tag, text_to_understand, language, logger):
    """Try to understand text"""
    client = WebsocketConnection(url, logger)
    try:
        yield from client.connect(app_id, app_key)
    except aiohttp.errors.ClientOSError as exp:
        return exp

    audio_type = 'audio/L16;rate=16000'

    client.send_message({'message': 'connect',
                         'device_id': '55555500000000000000000000000000',
                         'codec': audio_type
                         })

    _, msg = yield from client.receive()
    logger.debug(msg)  # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NDSP_APP_CMD',
        'language': language,
        'context_tag': context_tag,
    })

    client.send_message({
        'message': 'query_parameter',
        'transaction_id': 123,

        'parameter_name': 'REQUEST_INFO',
        'parameter_type': 'dictionary',

        'dictionary': {
            'application_data': {
                'text_input': text_to_understand,
            }
        }
    })

    client.send_message({
        'message': 'query_end',
        'transaction_id': 123,
    })

    ret = ""
    while True:
        _, msg = yield from client.receive()

        if msg['message'] == 'query_end':
            break
        ret = msg

    client.close()
    return ret
