import asyncio
import pyaudio
import itertools


class Recorder:
    """Record voice from mic"""

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
            if len(self.audio_queue):
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
