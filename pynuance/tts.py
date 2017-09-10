"""Provides Text-To-Speech functions"""
import asyncio
import logging

import pyaudio
try:
    import speex
except ImportError:
    speex = None

try:
    import opuslib.api as opus
except ImportError:
    opus = None

from pynuance.websocket import NCSWebSocketClient
from pynuance.libs.languages import LANGUAGES
from pynuance.libs.error import PyNuanceError

AUDIO_TYPES = [
    'audio/x-speex;mode=wb',
    'audio/opus;rate=16000',
    'audio/L16;rate=16000',
    'audio/16KADPCM;rate=16000'
]

COMMANDS = [
    'NVC_ASR_CMD',
    'NVC_DATA_UPLOAD_CMD',
    'NVC_RESET_USER_PROFILE_CMD',
    'NVC_TTS_CMD',
    'NDMP_TTS_CMD',
    'DRAGON_NLU_ASR_CMD',
    'DRAGON_NLU_APPSERVER_CMD',
    'DRAGON_NLU_DATA_UPLOAD_CMD',
    'DRAGON_NLU_RESET_USER_PROFILE_CMD',
    'NDSP_ASR_APP_CMD'
    'NDSP_APP_CMD',
    'NDSP_UPLOAD_DATA_CMD',
    'NDSP_DELETE_ALL_DATA_CMD',
]


def _get_opus_decoder_func(decoder):
    """Create function for Opus codec"""
    def decoder_func(msg):
        """Opus decoder function"""
        opus.decoder.decode(decoder, msg, len(msg), 1920, False, 1)

    return decoder_func


def text_to_speech(app_id, app_key, language, voice, codec, text,
                   user_id="pynuance_user", device_id="pynuance"):
    """Read a text with a given language, voice and code"""
    logger = logging.getLogger("pynuance").getChild("tts")
    voices_by_lang = dict([(l['code'], l['voice']) for l in LANGUAGES.values()])
    if language not in voices_by_lang:
        raise PyNuanceError("Language should be in "
                            "{}".format(", ".join(voices_by_lang.keys())))
    if voice not in voices_by_lang[language]:
        raise PyNuanceError("Voice should be in "
                            "{}".format(', '.join(voices_by_lang[language])))

    # Prepare ncs client
    ncs_client = NCSWebSocketClient("https://ws.dev.nuance.com/ws/v1/", app_id, app_key)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(do_synthesis(ncs_client, language, voice, codec,
                                         text, user_id, device_id))
    loop.stop()


@asyncio.coroutine
def do_synthesis(ncs_client, language, voice, codec, input_text,
                 user_id="pynuance_user", device_id="pynuance"):
    """The TTS function using Nuance Communications services"""
    logger = logging.getLogger("pynuance").getChild("tts")
    audio_player = pyaudio.PyAudio()

    if codec == "speex" and speex is None:
        print('ERROR: Speex encoding specified but python-speex module unavailable')
        return
    elif codec == "opus" and opus is None:
        print('ERROR: Opus encoding specified but python-opuslib module unavailable')
        return

    if codec == "speex":
        audio_type = 'audio/x-speex;mode=wb'
    elif codec == "opus":
        audio_type = 'audio/opus;rate=16000'
    else:
        audio_type = 'audio/L16;rate=16000'

    # Create stream player
    stream = audio_player.open(format=audio_player.get_format_from_width(2),
                               # format=p.get_format_from_width(wf.getsampwidth()),
                               channels=1,
                               # channels=wf.getnchannels(),
                               rate=16000,
                               # rate=wf.getframerate(),
                               output=True)

    # Prepare decoder
    if audio_type == 'audio/L16;rate=16000':
        decoder_func = None
    elif audio_type == 'audio/x-speex;mode=wb':
        decoder = speex.WBDecoder()  # pylint: disable=E1101  ; I don't know why...
        decoder_func = decoder.decode
    elif audio_type == 'audio/opus;rate=16000':
        decoder = opus.decoder.create(16000, 1)
        decoder_func = _get_opus_decoder_func(decoder)
    else:
        # TODO raise Error
        print('ERROR: Need to implement encoding for %s!' % audio_type)
        return

    try:
        yield from ncs_client.connect()

        session = yield from ncs_client.init_session(user_id, device_id, codec=audio_type)
        transaction = yield from session.begin_transaction(command='NVC_TTS_CMD',
                                                           language=language,
                                                           tts_voice=voice,
                                                           )
        request_info = {'dictionary': {'audio_id': 789,
                                       'tts_input': input_text,
                                       'tts_type': 'text'
                                       }
                        }
        yield from transaction.send_parameter(name='TEXT_TO_READ', type_='dictionary',
                                              value=request_info)
        yield from transaction.end(wait=False)
        # Get answer message 1
        yield from ncs_client.receive_json()
        # Check if we have a sound
        response = yield from ncs_client.receive_json()
        while response.get('message') == 'audio':
            # Read and play sound
            sound = yield from ncs_client.receive_bytes()
            if decoder_func is not None:
                sound = decoder_func(sound)
            logger.info("Start sentence")
            stream.write(sound)
            logger.info("End sentence")
            # Check if we have an other sound
            response = yield from ncs_client.receive_json()
            # response.get('message') == 'audio'
            # => New sound
            # response.get('message') == 'audio_end'
            # => No new sound
    finally:
        # Close stream and client
        stream.stop_stream()
        stream.close()
        audio_player.terminate()
        yield from ncs_client.close()
