"""Provides Speech-To-Text functions"""
import asyncio
import logging

from pynuance.websocket import NCSWebSocketClient
from pynuance.ncstransaction import NCSAudioTransfer
from pynuance.recorder import Recorder, listen_microphone
from pynuance.libs.common import WS_V1_URL


@asyncio.coroutine
def do_recognize(loop, ncs_client, language,  # pylint: disable=R0914,R0914
                 recorder, user_id="", device_id=""):
    """Main function for Speech-To-Text"""
    logger = logging.getLogger("pynuance").getChild("stt")

    audio_type = 'audio/x-speex;mode=wb'
    audio_type = "audio/opus;rate=%d" % recorder.rate
    try:
        yield from ncs_client.connect()
        session = yield from ncs_client.init_session(user_id, device_id, codec=audio_type)

        # https://developer.nuance.com/public/Help/SpeechKitFrameworkReference_Android/com/nuance/speechkit/RecognitionType.html
        # Should be "DICTATION", "SEARCH" or "TV"
        transaction = yield from session.begin_transaction(command='NVC_ASR_CMD',
                                                           language=language,
                                                           recognition_type='DICTATION',
                                                           )

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
        message = yield from ncs_client.receive_json()

        yield from transaction.wait_for_query_end()

    finally:
        yield from ncs_client.close()

    logger.debug(message)
    return message


def speech_to_text(app_id, app_key, language):
    """Speech to text from mic and return result.

    This function auto detect a silence
    """
    # Prepare ncs client
    ncs_client = NCSWebSocketClient(WS_V1_URL, app_id, app_key)

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # logger.debug("Get New event loop")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    with Recorder(loop=loop) as recorder:
        if loop.is_running():
            future = asyncio.run_coroutine_threadsafe(do_recognize(loop,
                                                                   ncs_client,
                                                                   language,
                                                                   recorder=recorder,
                                                                   ),
                                                      loop),
            output = future.result()  # pylint: disable=E1101
        else:
            output = loop.run_until_complete(do_recognize(
                loop,
                ncs_client,
                language,
                recorder=recorder,
                ))
            loop.stop()
    return output
