"""Provides Speech-To-Text functions"""
import asyncio
import binascii

import audioop

try:
    import speex
except ImportError:
    speex = None

from pynuance.logger import LOGGER_ROOT
from pynuance.websocket import WebsocketConnection
from pynuance.recorder import Recorder, silent_detection


_LOGGER_STT = LOGGER_ROOT.getChild("stt")


@asyncio.coroutine
def do_recognize(loop, url, app_id, app_key, language,  # pylint: disable=R0914,R0914
                 recorder, logger):
    """Main function for Speech-To-Text"""
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
    client = WebsocketConnection(url, _LOGGER_STT)
    yield from client.connect(app_id, app_key)

    # Init Nuance communication
    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type,
    })

    _, msg = yield from client.receive()
    # logger.info(msg)  # Should be a connected message

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NVC_ASR_CMD',  # 'NDSP_ASR_APP_CMD',
        'language': language,
        # https://developer.nuance.com/public/Help/SpeechKitFrameworkReference_Android/com/nuance/speechkit/RecognitionType.html
        # Should be "DICTATION", "SEARCH" or "TV"
        'recognition_type': 'DICTATION',
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

        yield from asyncio.wait((audiotask,),
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

    recorder.stop()

    client.send_message({
        'message': 'audio_end',
        'audio_id': 456,
    })

    msg_list = []
    while True:
        _, msg = yield from client.receive()
        logger.debug(msg)

        if msg['message'] == 'query_end':
            break
        else:
            msg_list.append(msg)

    client.close()

    return msg_list


def speech_to_text(app_id, app_key, language):
    """Speech to text from mic and return result.

    This function auto detect a silence
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    with Recorder(loop=loop) as recorder:
        output = loop.run_until_complete(do_recognize(
            loop,
            "https://ws.dev.nuance.com/v1/",
            app_id,
            binascii.unhexlify(app_key),
            language,
            recorder=recorder,
            logger=_LOGGER_STT,
            ))
        loop.stop()
    return output
