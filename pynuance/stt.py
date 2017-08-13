"""Provides Speech-To-Text functions"""
import asyncio
import binascii
import logging

from pynuance.websocket import WebsocketConnection, connection_handshake
from pynuance.recorder import Recorder, listen_microphone


@asyncio.coroutine
def do_recognize(loop, url, app_id, app_key, language,  # pylint: disable=R0914,R0914
                 recorder, logger):
    """Main function for Speech-To-Text"""
    # Websocket client
    client = WebsocketConnection(url, logger)
    yield from client.connect(app_id, app_key)

    # Init Nuance communication
    audio_type = 'audio/x-speex;mode=wb'
    client.send_message({
        'message': 'connect',
        'device_id': '55555500000000000000000000000000',
        'codec': audio_type,
    })

    _, msg = yield from client.receive()

    client.send_message({
        'message': 'query_begin',
        'transaction_id': 123,

        'command': 'NVC_ASR_CMD',
        'language': language,
        # https://developer.nuance.com/public/Help/SpeechKitFrameworkReference_Android/com/nuance/speechkit/RecognitionType.html
        # Should be "DICTATION", "SEARCH" or "TV"
        'recognition_type': 'DICTATION',
    })

    connection_handshake(client)

    audiotask = asyncio.ensure_future(recorder.dequeue())

    yield from listen_microphone(loop, client, recorder, audiotask, None, logger)

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


def speech_to_text(app_id, app_key, language, logger=None):
    """Speech to text from mic and return result.

    This function auto detect a silence
    """
    if logger is None:
        logger = logging.getLogger("pynuance").getChild("stt")
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
            logger=logger,
            ))
        loop.stop()
    return output
