import json
from asyncio import (
    AbstractEventLoop,
    Queue,
    QueueFull,
    create_task,
    get_running_loop,
    run,
)
from typing import AsyncGenerator, Literal

from google.cloud.speech import (
    RecognitionConfig,
    SpeechAsyncClient,
    StreamingRecognitionConfig,
    StreamingRecognitionResult,
    StreamingRecognizeRequest,
)
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from livetranslate.mic import RATE, MicrophoneStream


async def translate(client: AsyncOpenAI, transcript: str) -> str:
    prompt: str = """
    Translate this live transcription from Russian to Portuguese and add punctuation. Remember you
    are connected to the live stream so do your best job possible. As speaker speaks more context
    will be added - so don't worry about doing your best try. Return translation only.
    """
    n_last: int = 7
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

    content: str | None = response.choices[0].message.content
    if not content:
        return translation

    try:
        translation = str(json.loads(content)["translation"])
    except:
        pass

    return translation


async def consumer(queue: Queue[str], client: AsyncOpenAI):
    while True:
        item: str = await queue.get()
        translation = await translate(client, item)
        queue.task_done()
        if translation:
            print(translation)


async def make_requests(
    config: StreamingRecognitionConfig,
    audio_generator: AsyncGenerator[bytes, None],
) -> AsyncGenerator[StreamingRecognizeRequest, None]:
    yield StreamingRecognizeRequest(streaming_config=config)
    async for audio_content in audio_generator:
        yield StreamingRecognizeRequest(audio_content=audio_content)


async def main() -> None:
    loop: AbstractEventLoop = get_running_loop()

    # See http://g.co/cloud/speech/docs/languages
    language_code: Literal["ru-RU"] = "ru-RU"

    client: SpeechAsyncClient = SpeechAsyncClient()
    config = RecognitionConfig(
        encoding=RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=language_code,
    )

    streaming_config: StreamingRecognitionConfig = StreamingRecognitionConfig(
        config=config,
        interim_results=True,
        single_utterance=False,
    )

    queue: Queue[str] = Queue(maxsize=1)
    gpt_client: AsyncOpenAI = AsyncOpenAI()

    consumer_task = create_task(consumer(queue, gpt_client))

    async with MicrophoneStream(loop) as stream:
        audio_generator: AsyncGenerator[bytes, None] = stream.generator()
        requests = make_requests(streaming_config, audio_generator)
        response_stream = await client.streaming_recognize(requests=requests)
        async for response in response_stream:
            if not response.results:
                continue

            result: StreamingRecognitionResult = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            try:
                queue.put_nowait(transcript)
            except QueueFull:
                pass

    await consumer_task


if __name__ == "__main__":
    run(main())
