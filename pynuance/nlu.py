"""Provides Natural Language Understanding functions"""

import asyncio
import binascii

import aiohttp
try:
    import speex
except ImportError:
    speex = None

from pynuance.logger import LOGGER_ROOT
from pynuance.websocket import WebsocketConnection
from pynuance.libs.languages import NLU_LANGUAGES
from pynuance.libs.error import PyNuanceError
from pynuance.recorder import Recorder, silent_detection


_LOGGER_NLU = LOGGER_ROOT.getChild("nlu")

def understand_audio(app_id, app_key, context_tag, language):
    """NLU audio wrapper"""
    # transform language
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
            logger=_LOGGER_NLU,))
    # loop.close()
    if interpretations is False:
        # The user did not speak
        return {}
    else:
        return interpretations



@asyncio.coroutine
def _nlu_audio(loop, url, app_id, app_key, context_tag,  # pylint: disable=R0914
               language, recorder, logger):
    """Trying to understand audio"""
    audio = b''
    rawaudio = b''

    # Prepare audio
    rate = recorder.rate
    resampler = None

    if rate >= 16000:
        if rate != 16000:
            resampler = speex.SpeexResampler(1, rate, 16000)  # pylint: disable=E1101
    else:
        if rate != 8000:
            resampler = speex.SpeexResampler(1, rate, 8000)  # pylint: disable=E1101

    audio_type = 'audio/x-speex;mode=wb'
    encoder = speex.WBEncoder()  # pylint: disable=E1101

    # Websocket client
    client = WebsocketConnection(url, logger)
    yield from client.connect(app_id, app_key)

    # Init Nuance communication
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

    audiotask = asyncio.ensure_future(recorder.dequeue())
    receivetask = asyncio.ensure_future(client.receive())

    # Prepare silent vars
    silent_list = []
    first_silent_done = False
    while True:
        while len(rawaudio) > 320*recorder.channels*2:
            count = len(rawaudio)
            if count > 320*4*recorder.channels*2:
                count = 320*4*recorder.channels*2

            procsamples = b''
            if recorder.channels > 1:
                for i in range(0, count, 2*recorder.channels):
                    procsamples += rawaudio[i:i+1]
            else:
                procsamples = rawaudio[:count]

            rawaudio = rawaudio[count:]

            if resampler:
                audio += resampler.process(procsamples)
            else:
                audio += procsamples

        while len(audio) > encoder.frame_size*2:
            coded = encoder.encode(audio[:encoder.frame_size*2])
            client.send_audio(coded)
            audio = audio[encoder.frame_size*2:]

        yield from asyncio.wait((audiotask, receivetask),
                                return_when=asyncio.FIRST_COMPLETED,
                                loop=loop)

        # SILENT DETECTION
        ret, silent_list, first_silent_done = silent_detection(audio, silent_list,
                                                               first_silent_done, logger)
        if ret is False:
            return ret
        if ret is True:
            break

        if audiotask.done():
            more_audio = audiotask.result()
            rawaudio += more_audio
            audiotask = asyncio.ensure_future(recorder.dequeue())

        if receivetask.done():
            _, msg = receivetask.result()
            logger.debug(msg)

            if msg['message'] == 'query_end':
                client.close()
                return

            receivetask = asyncio.ensure_future(client.receive())

    recorder.stop()

    logger.debug("Send last message to Mix")
    client.send_message({
        'message': 'audio_end',
        'audio_id': 456,
    })

    interpretation = {}
    while True:
        yield from asyncio.wait((receivetask,), loop=loop)
        _, msg = receivetask.result()
        logger.debug(msg)

        if msg['message'] == 'query_end':
            break
        else:
            interpretation = msg

        receivetask = asyncio.ensure_future(client.receive())

    client.close()
    return interpretation



def understand_text(app_id, app_key, context_tag, language, text):
    """Nlu text wrapper"""
    # transform language
    nlu_language = NLU_LANGUAGES.get(language)
    if nlu_language is None:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(NLU_LANGUAGES.keys())))

    _LOGGER_NLU.debug("Text received: {}".format(text))
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        _LOGGER_NLU.debug("Get New event loop")
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
                  _LOGGER_NLU,
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
