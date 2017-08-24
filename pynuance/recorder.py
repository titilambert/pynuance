"""Provides class to listen to a microphone"""
import asyncio
import logging
import itertools

import audioop
import pyaudio
import opuslib

try:
    import speex
except ImportError:
    speex = None

# SILENT DETECTION
# TODO adjust it
FS_NB_CHUNK = 100
NB_CHUNK = 5
THRESHOLD = 500

AUDIO_FORMAT = pyaudio.paInt16
FRAME_SIZE = 320
SAMPLE_SIZE = pyaudio.get_sample_size(AUDIO_FORMAT)  # in bytes


@asyncio.coroutine
def listen_microphone(loop, audio_transfer, recorder, audiotask, audio_type=None):
    """Listen microphone and send audio to Nuance"""
    # Useful terminology reference:
    # https://larsimmisch.github.io/pyalsaaudio/terminology.html
    bytes_per_frame = recorder.channels * SAMPLE_SIZE
    audio_packet_min_size = FRAME_SIZE * bytes_per_frame
    audio_packet_max_size = 4 * audio_packet_min_size

    # Prepare audio
    if audio_type == "audio/x-speex;mode=wb":
        encoder = speex.WBEncoder()  # pylint: disable=E1101
    elif audio_type.startswith("audio/opus;rate"):
        encoder = opuslib.Encoder(fs=recorder.rate, channels=1,
                                  application=opuslib.api.constants.APPLICATION_VOIP)
    else:
        raise Exception(audio_type)

    # Prepare silent vars
    raw_audio = bytearray()
    mono_audio = bytearray()

    recorder.start()

    silent_list = []
    first_silent_done = False
    while True:
        while len(raw_audio) > audio_packet_min_size:
            count = min(len(raw_audio), audio_packet_max_size)
            mono_audio += convert_to_mono(raw_audio, count, recorder.channels, SAMPLE_SIZE)
            raw_audio = raw_audio[count:]

            while len(mono_audio) > FRAME_SIZE * SAMPLE_SIZE:
                audio_to_encode = bytes(mono_audio[:FRAME_SIZE*SAMPLE_SIZE])
                audio_encoded = encoder.encode(audio_to_encode, FRAME_SIZE)
                yield from audio_transfer.send_bytes(audio_encoded)
                mono_audio = mono_audio[FRAME_SIZE*SAMPLE_SIZE:]

        yield from asyncio.wait((audiotask,),
                                return_when=asyncio.FIRST_COMPLETED,
                                loop=loop)
        # SILENT DETECTION
        ret, silent_list, first_silent_done = silent_detection(mono_audio, silent_list,
                                                               first_silent_done)
        if ret is False:
            # TODO document this
            return ret
        if ret is True:
            # TODO document this
            break

        if audiotask.done():
            raw_audio += audiotask.result()
            audiotask = asyncio.ensure_future(recorder.audio_queue.get())

    return


def silent_detection(audio, silent_list, first_silent_done):
    """Analyse audio chunk to determine if this is a silent

    return False: the user did NOT speak
    return None: the user is speaking or we are waiting for it
    return True: the user had finished to speack
    """
    logger = logging.getLogger("pynuance").getChild("nlu").getChild("silent")
    # Get rms for this chunk
    audio_rms = audioop.rms(audio, 2)
    # Detect first silent
    if first_silent_done is False:
        logger.debug("Audio level: %s", audio_rms)
        if audio_rms < THRESHOLD:
            logger.debug("Waiting for user speaking")
            silent_list.append(True)
        else:
            logger.debug("User is maybe starting to speak")
            silent_list.append(False)
        if len([s for s in silent_list if s is False]) > 5:
            logger.debug("User is starting to speak")
            silent_list = []
            first_silent_done = True
        if len(silent_list) > FS_NB_CHUNK:
            logger.debug("The user did NOT speak")
            return False, silent_list, first_silent_done
    else:
        silent_list.append(True if audio_rms < THRESHOLD else False)
        if len(silent_list) > NB_CHUNK:
            logger.debug("The user is speaking. Level: %d", audio_rms)
            silent_list.pop(0)
        if len(silent_list) == NB_CHUNK and all(silent_list):
            logger.debug("The user has finished to speak")
            return True, silent_list, first_silent_done
    return None, silent_list, first_silent_done


class Recorder:
    """Audio recorder class"""

    def __init__(self, device_index=None, rate=None, channels=None,
                 loop=None, auto_start=False):
        # Audio configuration
        self._audio = pyaudio.PyAudio()

        if device_index is None:
            device_index = self.pick_default_device_index()

        self._device_index = device_index

        if rate is None or channels is None:
            self.pick_default_parameters()
        else:
            self.rate = rate
            self.channels = channels

        self._stream = None

        # Event loop
        if loop is None:
            loop = asyncio.get_event_loop()

        self._loop = loop
        self.audio_queue = asyncio.Queue()
        self.auto_start = auto_start

    def start(self):
        """Start the recorder"""
        self._stream.start_stream()

    def stop(self):
        """Stop the recorder"""
        self._stream.stop_stream()

    def __enter__(self):
        self._stream = self._audio.open(
            self.rate,
            self.channels,
            AUDIO_FORMAT,
            input=True,
            input_device_index=self._device_index,
            start=self.auto_start,
            stream_callback=self.callback)
        return self

    def __exit__(self, error_type, value, traceback):
        if self._stream is not None:
            if not self._stream.is_stopped():
                self._stream.stop_stream()
            self._stream.close()
        if self._audio is not None:
            self._audio.terminate()

    def callback(self, in_data, *_args):  # pylint: disable=W0613
        asyncio.run_coroutine_threadsafe(self.audio_queue.put(in_data), self._loop)
        return (None, pyaudio.paContinue)

    def pick_default_device_index(self):
        try:
            device_info = self._audio.get_default_input_device_info()
            return device_info['index']
        except IOError:
            raise RuntimeError('No Recording Devices Found')

    def pick_default_parameters(self):
        """ Pick compatible rates and channels in preferred order.

        16kHz is the preferred sampling rate, as it yields both good transfer
        speed and recognition results.

        Mono audio is also preferred, as stereo doubles the bandwidth,
        typically without any significant recognition improvement.
        """
        rates = [
            16000,
            24000,
            48000,
            12000,
            8000,
        ]
        channels = [1, 2]

        # Add device spefic information
        info = self._audio.get_device_info_by_index(self._device_index)
        rates.append(info['defaultSampleRate'])
        channels.append(info['maxInputChannels'])

        for (rate, channel) in itertools.product(rates, channels):
            if self._audio.is_format_supported(rate,
                                               input_device=self._device_index,
                                               input_channels=channel,
                                               input_format=pyaudio.paInt16):
                (self.rate, self.channels) = (rate, channel)
                break
        else:
            # If no (rate, channel) combination is found, raise an error
            error = "Couldn't find recording parameters for device %s" % self._device_index
            raise RuntimeError(error)


def convert_to_mono(raw_audio, count, channels, sample_size):
    """Convert a subset of a raw audio buffer (up to `count` bytes)
    into single-channel (mono) audio.
    """
    mono_audio = bytearray()
    if channels == 1:
        mono_audio += raw_audio[:count]
    else:
        for i in range(0, count, channels * sample_size):
            mono_audio += raw_audio[i:i+sample_size]
    return mono_audio
