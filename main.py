import asyncio
from asyncio import AbstractEventLoop

import json

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from google.cloud import speech

from typing import AsyncGenerator

import pyaudio

RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

client = AsyncOpenAI()


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
        self._buff = asyncio.Queue()
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

        return self

    async def __aexit__(
        self,
        type: object,
        value: object,
        traceback: object,
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
        in_data: object,
        frame_count: int,
        time_info: object,
        status_flags: object,
    ) -> object:
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
        return None, pyaudio.paContinue

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
                except asyncio.QueueEmpty:
                    break

            yield b"".join(data)


async def translate(transcript: str) -> str:
    prompt = """
    Translate this live transcription from Russian to Portuguese and add punctuation. Remember you
    are connected to the live stream so do your best job possible. As speaker speaks more context
    will be added - so don't worry about doing your best try. Return translation only.
    """
    n_last = 7
    last_words: str = " ".join(transcript.split(" ")[-n_last:])

    response: ChatCompletion = await client.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        seed=1,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant designed to output JSON.",
            },
            {"role": "user", "content": prompt},
            {"role": "user", "content": last_words},
        ],
    )
    translation: str = ""
    try:
        translation = str(
            json.loads(response.choices[0].message.content)["translation"]
        )
    except:
        pass

    return translation


async def consumer(queue: asyncio.Queue[str]):
    while True:
        item: str = await queue.get()
        translation = await translate(item)
        queue.task_done()
        if translation:
            print(translation)


async def make_requests(
    config: speech.StreamingRecognitionConfig,
    audio_generator: AsyncGenerator[bytes, None],
) -> AsyncGenerator[speech.StreamingRecognizeRequest, None]:
    yield speech.StreamingRecognizeRequest(streaming_config=config)
    async for audio_content in audio_generator:
        yield speech.StreamingRecognizeRequest(audio_content=audio_content)


async def main() -> None:
    loop: AbstractEventLoop = asyncio.get_running_loop()

    """Transcribe speech from audio file."""
    # See http://g.co/cloud/speech/docs/languages
    language_code = "ru-RU"

    client = speech.SpeechAsyncClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True, single_utterance=False,
    )

    queue = asyncio.Queue(maxsize=1)
    consumer_task = asyncio.create_task(consumer(queue))

    async with MicrophoneStream(loop, RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = make_requests(streaming_config, audio_generator)
        response_stream = await client.streaming_recognize(requests=requests)
        async for response in response_stream:
            if not response.results:
                continue

            result = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            try:
                queue.put_nowait(transcript)
            except asyncio.QueueFull:
                pass

    await consumer_task


if __name__ == "__main__":
    asyncio.run(main())
