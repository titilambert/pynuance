import asyncio
import binascii

from pynuance.logger import LOGGER_ROOT

from pynuance.websocket import WebsocketConnection
from pynuance.languages import NLU_LANGUAGES


_LOGGER_NLU = LOGGER_ROOT.getChild("nlu")


def nlu_text(app_id, app_key, context_tag, language, text):
    """Nlu text wrapper"""
    # Reload config from file because we are in an other Process
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
                  language,
                  _LOGGER_NLU,
                  ))
    # loop.close()
    if interpretations is False:
        # The user did not speak
        return {}
    else:
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
    print(ret)
    return ret
