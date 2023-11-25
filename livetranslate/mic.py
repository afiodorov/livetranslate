from asyncio import AbstractEventLoop, Queue, QueueEmpty
from typing import AsyncGenerator

import pyaudio

RATE: int = 16_000
CHUNK: int = RATE // 10  # 100 ms


class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(
        self, loop: AbstractEventLoop, rate: int = RATE, chunk: int = CHUNK
    ) -> None:
        """The audio -- and generator -- is guaranteed to be on the main thread."""
        self._rate = rate
        self._chunk = chunk
        self.loop: AbstractEventLoop = loop

        # Create a thread-safe buffer of audio data
        self._buff = Queue()
        self.closed = True

    async def __aenter__(self) -> "MicrophoneStream":
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )
        self.closed = False
        self._audio_stream.start_stream()

        return self

    async def __aexit__(
        self,
        *_,
    ) -> None:
        """Closes the stream, regardless of whether the connection was lost or not."""
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        await self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self,
        in_data: bytes | None,
        *_,
    ) -> tuple[bytes | None, int]:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
            in_data: The audio data as a bytes object
            frame_count: The number of frames captured
            time_info: The time information
            status_flags: The status flags

        Returns:
            The audio data as a bytes object
        """
        self.loop.call_soon_threadsafe(self._buff.put_nowait, in_data)

        return in_data, pyaudio.paContinue

    async def generator(self) -> AsyncGenerator[bytes, None]:
        """Generates audio chunks from the stream of audio data in chunks.

        Args:
            self: The MicrophoneStream object

        Returns:
            A generator that outputs audio chunks.
        """
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = await self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get_nowait()
                    if chunk is None:
                        return
                    data.append(chunk)
                except QueueEmpty:
                    break

            yield b"".join(data)
