"""Provides Natural Language Understanding functions"""

import asyncio
import binascii
import logging
import pyaudio

import aiohttp

from pynuance.libs.languages import NLU_LANGUAGES
from pynuance.libs.error import PyNuanceError
from pynuance.recorder import Recorder, listen_microphone
from pynuance.websocket import NCSWebSocketClient
from pynuance.ncstransaction import NCSAudioTransfer

AUDIO_FORMAT = pyaudio.paInt16
FRAME_SIZE = 320
SAMPLE_SIZE = pyaudio.get_sample_size(AUDIO_FORMAT)  # in bytes


def understand_audio(app_id, app_key, context_tag, language, logger=None):
    """NLU audio wrapper"""
    # transform language
    if logger is None:
        logger = logging.getLogger("pynuance").getChild("nlu").getChild("audio")
    nlu_language = NLU_LANGUAGES.get(language)
    if nlu_language is None:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(NLU_LANGUAGES.keys())))

    # Prepare ncs client
    ncs_client = NCSWebSocketClient("https://ws.dev.nuance.com/ws/v1/", app_id, app_key)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # TODO: change it to variable
    user_id = "user1"

    interpretations = {}
    with Recorder(loop=loop) as recorder:
        interpretations = loop.run_until_complete(_nlu_audio(
                ncs_client,
                loop,
                recorder,
                user_id,
                context_tag=context_tag,
                language=nlu_language))
    # loop.close()
    if interpretations is False:
        # The user did not speak
        return {}

    return interpretations


@asyncio.coroutine
def _nlu_audio(ncs_client, loop, recorder, user_id, context_tag, language):
    """Trying to understand audio"""
    # Websocket client
    logger = logging.getLogger("pynuance").getChild("nlu").getChild("audio")

    audio_type = "audio/opus;rate=%d" % recorder.rate

    DEVICE_ID = 'device_id'

    try:
        yield from ncs_client.connect()
        session = yield from ncs_client.init_session(user_id, DEVICE_ID, codec=audio_type)
        transaction = yield from session.begin_transaction(command='NDSP_ASR_APP_CMD',
                                                           language=language,
                                                           context_tag=context_tag)

        audio_transfer = NCSAudioTransfer(id_=session.get_new_audio_id(), session=session)
        yield from transaction.send_parameter(name='AUDIO_INFO', type_='audio',
                                              value=audio_transfer.info)

        # We end the transaction here, but we will only have a 'query_end' response
        # back when the audio transfer and ASR/NLU are done.
        yield from transaction.end(wait=False)
        yield from audio_transfer.begin()

        audiotask = asyncio.ensure_future(recorder.audio_queue.get())

        recorder.start()
        yield from listen_microphone(loop, audio_transfer,
                                     recorder, audiotask, audio_type)
        recorder.stop()

        audiotask.cancel()
        yield from audio_transfer.end(wait=False)
        yield from ncs_client.receive_json()

        yield from transaction.wait_for_query_end()
        message = transaction.response

    finally:
        yield from ncs_client.close()

    return message


def understand_text(app_id, app_key, user_id, context_tag, text, language):
    """Nlu text wrapper"""
    logger = logging.getLogger("pynuance").getChild("nlu").getChild("text")
    # transform language
    nlu_language = NLU_LANGUAGES.get(language)
    if nlu_language is None:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(NLU_LANGUAGES.keys())))

    logger.debug("Text received: {}".format(text))
    # Prepare ncs client
    ncs_client = NCSWebSocketClient("https://ws.dev.nuance.com/ws/v1/", app_id, app_key)

    # Get asyncio Loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # Run nlu text
    interpretations = loop.run_until_complete(_nlu_text(
        ncs_client,
        user_id,
        context_tag=context_tag,
        text_to_understand=text,
        language=nlu_language))

    return interpretations


@asyncio.coroutine
def _nlu_text(ncs_client, user_id, context_tag, text_to_understand, language='eng-USA'):
    """Try to understand text"""
    request_info = {
        'dictionary': {
            'application_data': {
                'text_input': text_to_understand,
            },
        },
    }
    try:
        # TODO: change it to variable
        DEVICE_ID = 'MIX_WS_PYTHON_SAMPLE_APP'
        yield from ncs_client.connect()
        session = yield from ncs_client.init_session(user_id, DEVICE_ID)
        transaction = yield from session.begin_transaction(command='NDSP_APP_CMD',
                                                           language=language,
                                                           context_tag=context_tag)
        yield from transaction.send_parameter(name='REQUEST_INFO', type_='dictionary',
                                              value=request_info)
        message = yield from transaction.end()
    finally:
        yield from ncs_client.close()
    return transaction.response
