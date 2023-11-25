import argparse
import json
import os
from asyncio import AbstractEventLoop, Queue, TaskGroup, get_running_loop, run
from collections import Counter
from typing import AsyncGenerator
from urllib.parse import urlencode

import websockets
from google.cloud.translate import TranslationServiceAsyncClient
from websockets.client import WebSocketClientProtocol

from livetranslate.mic import RATE, MicrophoneStream
from livetranslate.translate import translate_text


async def consumer(
    queue: Queue[tuple[int, str, bool]],
    source_language: str,
    target_language: str,
    translation_client: TranslationServiceAsyncClient,
) -> None:
    prev_translation: str = ""

    while True:
        transcript: str = ""
        speaker: int

        speaker, transcript, is_final = await queue.get()
        translation: str = await translate_text(
            translation_client, transcript, source_language, target_language
        )
        queue.task_done()

        if not translation:
            continue

        pad = " " * (len(prev_translation) - len(translation))
        if is_final:
            print(f"\r{speaker}: {translation}{pad}\n", end="", flush=True)
        else:
            print(f"\r{speaker}: {translation}{pad}", end="", flush=True)

        prev_translation = translation


async def sender(
    ws: WebSocketClientProtocol, audio_generator: AsyncGenerator[bytes, None]
) -> None:
    async for mic_data in audio_generator:
        await ws.send(mic_data)


async def receiver(
    ws: WebSocketClientProtocol, queue: Queue[tuple[int, str, bool]]
) -> None:
    async for msg in ws:
        res = json.loads(msg)

        transcript: str = (
            res.get("channel", {}).get("alternatives", [{}])[0].get("transcript", "")
        )

        if not transcript:
            continue

        counter: Counter = Counter(
            [x["speaker"] for x in res["channel"]["alternatives"][0]["words"]]
        )

        if not counter:
            continue

        speaker: int = counter.most_common(1)[0][0]

        if queue.full():
            _ = await queue.get()
            queue.task_done()
        await queue.put((speaker, transcript, bool(res["is_final"])))


async def main(source_language: str, target_language: str) -> None:
    # program_state: ProgramState = register()

    loop: AbstractEventLoop = get_running_loop()

    queue: Queue[tuple[int, str, bool]] = Queue(maxsize=1)

    params: dict[str, str] = {
        "diarize": "true",
        "punctuate": "true",
        "filler_words": "true",
        "interim_results": "true",
        "language": source_language.split("-")[0],
        "encoding": "linear16",
        "sample_rate": str(RATE),
    }

    if params["language"] in ("en", "fr", "de", "hi", "pt", "es"):
        params["tier"] = "nova"
        params["model"] = "2-general"

    query_string = urlencode(params)
    deepgram_url = f"wss://api.deepgram.com/v1/listen?{query_string}"
    key = os.environ["DEEPGRAM_API_KEY"]

    translation_client = TranslationServiceAsyncClient()

    async with MicrophoneStream(loop) as stream, websockets.connect(
        deepgram_url, extra_headers={"Authorization": f"Token {key}"}
    ) as ws, TaskGroup() as tg:
        tg.create_task(
            consumer(queue, source_language, target_language, translation_client)
        )

        tg.create_task(receiver(ws, queue))
        tg.create_task(sender(ws, stream.generator()))


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
