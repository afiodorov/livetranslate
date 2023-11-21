import argparse
from asyncio import (
    AbstractEventLoop,
    CancelledError,
    Queue,
    create_task,
    get_running_loop,
    run,
)
from typing import AsyncGenerator, AsyncIterable

from google.api_core.exceptions import ClientError, ServerError
from google.api_core.retry_async import AsyncRetry
from google.cloud.speech import (
    RecognitionConfig,
    SpeechAsyncClient,
    StreamingRecognitionConfig,
    StreamingRecognitionResult,
    StreamingRecognizeRequest,
    StreamingRecognizeResponse,
)
from Levenshtein import ratio

from livetranslate.mic import RATE, MicrophoneStream
from livetranslate.translate import translate_text


async def consumer(queue: Queue[str], source_language: str, target_language: str):
    prev_translation: str = ""
    while True:
        transcript: str = await queue.get()
        translation = await translate_text(transcript, source_language, target_language)
        queue.task_done()

        if translation:
            if ratio(translation, prev_translation) >= 0.95:
                pad: str = " " * (len(prev_translation) - len(translation))
                print(f"\r{translation}{pad}", end="", flush=True)
            else:
                print(f"\n{translation}", end="", flush=True)

            prev_translation = translation


async def make_requests(
    config: StreamingRecognitionConfig,
    audio_generator: AsyncGenerator[bytes, None],
) -> AsyncGenerator[StreamingRecognizeRequest, None]:
    yield StreamingRecognizeRequest(streaming_config=config)
    async for audio_content in audio_generator:
        yield StreamingRecognizeRequest(audio_content=audio_content)


async def main(source_language: str, target_language: str) -> None:
    loop: AbstractEventLoop = get_running_loop()

    client: SpeechAsyncClient = SpeechAsyncClient()
    config = RecognitionConfig(
        encoding=RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=source_language,
        use_enhanced=True,
        model="phone_call",
    )

    streaming_config: StreamingRecognitionConfig = StreamingRecognitionConfig(
        config=config,
        interim_results=True,
        single_utterance=False,
    )

    queue: Queue[str] = Queue(maxsize=1)

    create_task(consumer(queue, source_language, target_language))

    async with MicrophoneStream(loop) as stream:
        audio_generator: AsyncGenerator[bytes, None] = stream.generator()

        while True:
            requests = make_requests(streaming_config, audio_generator)
            response_stream = await client.streaming_recognize(
                requests=requests,
                retry=AsyncRetry(
                    timeout=1, predicate=lambda e: isinstance(e, ServerError)
                ),
            )
            await keep_transcribing(response_stream, queue)


async def keep_transcribing(
    response_stream: AsyncIterable[StreamingRecognizeResponse],
    queue: Queue[str],
) -> None:
    try:
        async for response in response_stream:
            if not response.results:
                continue

            result: StreamingRecognitionResult = response.results[0]
            if not result.alternatives:
                continue

            transcript = result.alternatives[0].transcript

            if queue.full():
                _ = await queue.get()
                queue.task_done()
            await queue.put(transcript)
    except (ServerError, ClientError):
        pass
    except CancelledError:
        if (
            response_stream._call._cython_call._status.details()
            == "Locally cancelled by application!"
        ):
            raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for language translation")

    parser.add_argument(
        "-s",
        "--source",
        default="ru-RU",
        type=str,
        help="Source language (default: ru-RU). For language codes, see http://g.co/cloud/speech/docs/languages",
    )
    parser.add_argument(
        "-t",
        "--target",
        default="pt-BR",
        type=str,
        help="Target language (default: pt-BR). For language codes, see http://g.co/cloud/speech/docs/languages",
    )

    args = parser.parse_args()

    run(main(args.source, args.target))
