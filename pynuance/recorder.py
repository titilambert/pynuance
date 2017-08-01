"""Provides class to listen to a microphone"""
import asyncio
import itertools

import audioop
import pyaudio
try:
    import speex
except ImportError:
    speex = None

# SILENT DETECTION
# TODO adjust it
FS_NB_CHUNK = 100
NB_CHUNK = 5
THRESHOLD = 500


@asyncio.coroutine
def listen_microphone(loop, client, recorder, audiotask, receivetask=None, logger=None):
    """Listen microphone and send audio to Nuance"""
    # Prepare silent vars
    audio = b''
    rawaudio = b''

    encoder = speex.WBEncoder()  # pylint: disable=E1101

    # Prepare audio
    rate = recorder.rate
    resampler = None

    if rate >= 16000:
        if rate != 16000:
            resampler = speex.SpeexResampler(1, rate, 16000)  # pylint: disable=E1101
    else:
        if rate != 8000:
            resampler = speex.SpeexResampler(1, rate, 8000)  # pylint: disable=E1101

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

        if receivetask is not None:
            yield from asyncio.wait((audiotask, receivetask),
                                    return_when=asyncio.FIRST_COMPLETED,
                                    loop=loop)
        else:
            yield from asyncio.wait((audiotask,),
                                    return_when=asyncio.FIRST_COMPLETED,
                                    loop=loop)

        # SILENT DETECTION
        ret, silent_list, first_silent_done = silent_detection(audio, silent_list,
                                                               first_silent_done, logger)
        if ret is False:
            # TODO document this
            return ret
        if ret is True:
            # TODO document this
            break

        if audiotask.done():
            more_audio = audiotask.result()
            rawaudio += more_audio
            audiotask = asyncio.ensure_future(recorder.dequeue())

        if receivetask is not None and receivetask.done():
            _, msg = receivetask.result()
            logger.debug(msg)

            if msg['message'] == 'query_end':
                client.close()
                return

            receivetask = asyncio.ensure_future(client.receive())


def silent_detection(audio, silent_list, first_silent_done, logger):
    """Analyse audio chunk to determine if this is a silent

    return False: the user did NOT speak
    return None: the user is speaking or we are waiting for it
    return True: the user had finished to speack
    """
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
    """Record voice from microphone"""

    def __init__(self, device_index=None, rate=None, channels=None, loop=None):

        # Audio configuration
        self.audio = pyaudio.PyAudio()

        if device_index is None:
            self.pick_default_device_index()
        else:
            self.device_index = device_index

        if rate is None or channels is None:
            self.pick_default_parameters()
        else:
            self.rate = rate
            self.channels = channels

        self.recstream = None

        # Event loop
        if loop:
            self.loop = loop
        else:
            self.loop = asyncio.get_event_loop()
        self.queue_event = asyncio.Event(loop=self.loop)
        self.audio_queue = []

    def __enter__(self):
        self.recstream = self.audio.open(
            self.rate,
            self.channels,
            pyaudio.paInt16,
            input=True,
            input_device_index=self.device_index,
            stream_callback=self.callback)
        return self

    def __exit__(self, error_type, value, traceback):
        if self.recstream is not None:
            self.recstream.close()

    def enqueue(self, audio):  # pylint: disable=C0111
        self.audio_queue.append(audio)
        self.queue_event.set()

    @asyncio.coroutine
    def dequeue(self):  # pylint: disable=C0111
        while True:
            self.queue_event.clear()
            if self.audio_queue:
                return self.audio_queue.pop(0)
            yield from self.queue_event.wait()

    def callback(self, in_data, frame_count, time_info, status_flags):  # pylint: disable=W0613
        """Callback function"""
        self.loop.call_soon_threadsafe(self.enqueue, in_data)
        return (None, pyaudio.paContinue)

    def pick_default_device_index(self):  # pylint: disable=C0111
        try:
            device_info = self.audio.get_default_input_device_info()
            self.device_index = device_info['index']
        except IOError:
            raise RuntimeError("No Recording Devices Found")

    def pick_default_parameters(self):  # pylint: disable=C0111
        rates = [
            16000,
            32000,
            48000,
            96000,
            192000,
            22050,
            44100,
            88100,
            8000,
            11025,
        ]
        channels = [1, 2]

        # Add device spefic information
        info = self.audio.get_device_info_by_index(self.device_index)
        rates.append(info['defaultSampleRate'])
        channels.append(info['maxInputChannels'])

        for (rate, channel) in itertools.product(rates, channels):
            if self.audio.is_format_supported(rate,
                                              input_device=self.device_index,
                                              input_channels=channel,
                                              input_format=pyaudio.paInt16):
                (self.rate, self.channels) = (rate, channel)
                break
        else:
            # If no (rate, channel) combination is found, raise an error
            error = "Couldn't find recording parameters for device {}".format(self.device_index)
            raise RuntimeError(error)

    def stop(self):
        """Kill recorder"""
        self.audio.terminate()
