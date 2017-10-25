"""Provides Natural Language Understanding functions"""

import asyncio
import logging
import pyaudio

from pynuance.libs.languages import NLU_LANGUAGES
from pynuance.libs.error import PyNuanceError
from pynuance.recorder import Recorder, listen_microphone
from pynuance.websocket import NCSWebSocketClient
from pynuance.ncstransaction import NCSAudioTransfer
from pynuance.libs.common import WS_V1_URL

AUDIO_FORMAT = pyaudio.paInt16
FRAME_SIZE = 320
SAMPLE_SIZE = pyaudio.get_sample_size(AUDIO_FORMAT)  # in bytes


def understand_audio(app_id, app_key, context_tag, language,
                     user_id="pynuance_user", device_id="pynuance"):
    """NLU audio wrapper"""
    logger = logging.getLogger("pynuance").getChild("nlu").getChild("audio")
    # transform language
    nlu_language = NLU_LANGUAGES.get(language)
    if nlu_language is None:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(NLU_LANGUAGES.keys())))

    # Prepare ncs client
    ncs_client = NCSWebSocketClient(WS_V1_URL, app_id, app_key)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    interpretations = {}
    with Recorder(loop=loop) as recorder:
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(_nlu_audio(ncs_client,
                                                                 loop,
                                                                 recorder,
                                                                 context_tag=context_tag,
                                                                 language=nlu_language,
                                                                 user_id=user_id,
                                                                 device_id=device_id,
                                                                 ),
                                                      loop)
            interpretations = future.result()
        else:
            interpretations = loop.run_until_complete(_nlu_audio(
                ncs_client,
                loop,
                recorder,
                context_tag=context_tag,
                language=nlu_language,
                user_id=user_id,
                device_id=device_id,
                ))
            loop.stop()
    # .close()
    if interpretations is False:
        # The user did not speak
        return {}

    return interpretations


@asyncio.coroutine
def _nlu_audio(ncs_client, loop, recorder, context_tag, language,
               user_id="pynuance_user", device_id="pynuance"):
    """Trying to understand audio"""
    logger = logging.getLogger("pynuance").getChild("nlu").getChild("audio")
    # Websocket client
    audio_type = "audio/opus;rate=%d" % recorder.rate

    try:
        yield from ncs_client.connect()
        session = yield from ncs_client.init_session(user_id, device_id, codec=audio_type)
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
        logger.debug("Start listening")
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


def understand_text(app_id, app_key, context_tag, text, language,
                    user_id="pynuance_user", device_id="pynuance"):
    """Nlu text wrapper"""
    logger = logging.getLogger("pynuance").getChild("nlu").getChild("text")
    # transform language
    nlu_language = NLU_LANGUAGES.get(language)
    if nlu_language is None:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(NLU_LANGUAGES.keys())))

    logger.debug("Text received: {}".format(text))
    # Prepare ncs client
    ncs_client = NCSWebSocketClient(WS_V1_URL, app_id, app_key)

    # Get asyncio Loop
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # Run nlu text
    if loop.is_running():
        future = asyncio.run_coroutine_threadsafe(_nlu_text(ncs_client,
                                                            context_tag=context_tag,
                                                            text_to_understand=text,
                                                            language=nlu_language,
                                                            user_id=user_id,
                                                            device_id=device_id),
                                                  loop)
        interpretations = future.result()
    else:
        interpretations = loop.run_until_complete(_nlu_text(
            ncs_client,
            context_tag=context_tag,
            text_to_understand=text,
            language=nlu_language,
            user_id=user_id,
            device_id=device_id))

    return interpretations


@asyncio.coroutine
def _nlu_text(ncs_client, context_tag, text_to_understand, language='eng-USA',
              user_id="pynuance_user", device_id="pynuance"):
    """Try to understand text"""
    request_info = {
        'dictionary': {
            'application_data': {
                'text_input': text_to_understand,
            },
        },
    }
    try:
        yield from ncs_client.connect()
        session = yield from ncs_client.init_session(user_id, device_id)
        transaction = yield from session.begin_transaction(command='NDSP_APP_CMD',
                                                           language=language,
                                                           context_tag=context_tag)
        yield from transaction.send_parameter(name='REQUEST_INFO', type_='dictionary',
                                              value=request_info)
        yield from transaction.end()
    finally:
        yield from ncs_client.close()
    return transaction.response
