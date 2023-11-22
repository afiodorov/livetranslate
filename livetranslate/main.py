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
from openai import AsyncOpenAI

from livetranslate.flow import ProgramState, register
from livetranslate.lang_utils import merge
from livetranslate.mic import RATE, MicrophoneStream
from livetranslate.translate import translate_text

prompt: str = """
You're helping another AI translator. Your job is to unite these 2 translation into a single coherent
properly formatted translation with at most 2 sentences. Reply in {{target_language}}.
"""


async def consumer(
    queue: Queue[str],
    source_language: str,
    target_language: str,
    gpt_client: AsyncOpenAI,
):
    prev_translation: str = ""

    while True:
        translation: str = ""

        transcript: str = await queue.get()
        translation = await translate_text(transcript, source_language, target_language)
        queue.task_done()

        if not translation:
            continue

        # response: ChatCompletion = await gpt_client.chat.completions.create(
        #     model="gpt-3.5-turbo-1106",
        #     seed=120,
        #     response_format={"type": "json_object"},
        #     messages=[
        #         {
        #             "role": "system",
        #             "content": 'You are a helpful assistant designed to output JSON of a combined translation'
        #         },
        #         {"role": "user", "content": prompt.replace("{{target_language}}", target_language, 1)},
        #         {"role": "user", "content": prev_translation},
        #         {"role": "user", "content": translation},
        #     ],
        # )

        # content: str | None = response.choices[0].message.content
        # if not content:
        #     continue

        # try:
        #     for v in json.loads(content).values():
        #         if isinstance(v, str) and v.strip():
        #             translation = v.strip()
        # except:
        #     continue

        # if translation == "":
        #     breakpoint()
        #     pass

        merged, is_merged = merge(prev_translation, translation)
        if is_merged:
            translation = merged

        # translation = last_words(translation, 15)

        pad: str = " " * (len(prev_translation) - len(translation))
        print(f"\r{translation}{pad}", end="", flush=True)

        prev_translation = translation


async def make_requests(
    config: StreamingRecognitionConfig,
    audio_generator: AsyncGenerator[bytes, None],
) -> AsyncGenerator[StreamingRecognizeRequest, None]:
    yield StreamingRecognizeRequest(streaming_config=config)
    async for audio_content in audio_generator:
        yield StreamingRecognizeRequest(audio_content=audio_content)


async def main(source_language: str, target_language: str) -> None:
    program_state: ProgramState = register()

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

    gpt_client: AsyncOpenAI = AsyncOpenAI()

    create_task(consumer(queue, source_language, target_language, gpt_client))

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
            await keep_transcribing(response_stream, queue, program_state)


async def keep_transcribing(
    response_stream: AsyncIterable[StreamingRecognizeResponse],
    queue: Queue[str],
    program_state: ProgramState,
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
        if program_state.keyboard_interrupt:
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
