import argparse
import json
import os
import sys
from asyncio import (
    AbstractEventLoop,
    Queue,
    Task,
    TaskGroup,
    get_running_loop,
    new_event_loop,
    set_event_loop,
)
from collections import Counter, deque
from threading import Thread
from typing import AsyncGenerator, Callable
from urllib.parse import urlencode

import websockets
from google.cloud.translate import TranslationServiceAsyncClient
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from websockets.client import WebSocketClientProtocol

from livetranslate.gui import start_gui
from livetranslate.mic import RATE, MicrophoneStream
from livetranslate.translate import (
    deepl_language,
    translate_text_deepl,
    translate_text_google,
)


async def consumer(
    queue: Queue[tuple[int, str, bool]],
    source_language: str,
    target_language: str,
    translation_client: TranslationServiceAsyncClient | None,
    update_subtitles: Callable[[str], None],
) -> None:
    context: deque[str] = deque(maxlen=3)

    while True:
        transcript: str = ""

        _, transcript, is_final = await queue.get()
        if translation_client:
            translation: str = await translate_text_google(
                translation_client, transcript, source_language, target_language
            )
        elif source_language != target_language:
            translation: str = await translate_text_deepl(
                transcript, source_language, target_language, " ".join(context)
            )
        else:
            translation = transcript

        queue.task_done()

        if not translation:
            continue

        if is_final:
            update_subtitles(translation)
            context.append(transcript)
        else:
            update_subtitles(translation)


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


async def main(
    source_language: str,
    target_language: str,
    update_subtitles: Callable[[str], None],
    use_google_translate: bool,
) -> None:
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
    elif params["language"] in (
        "da",
        "nl",
        "it",
        "ja",
        "ko",
        "no",
        "pl",
        "sv",
        "ta",
        "taq",
    ):
        params["model"] = "enhanced"

    query_string: str = urlencode(params)
    deepgram_url: str = f"wss://api.deepgram.com/v1/listen?{query_string}"
    key: str = os.environ["DEEPGRAM_API_KEY"]

    translation_client: None | TranslationServiceAsyncClient = None

    deepl_source = deepl_language(source_language)
    deepl_target = deepl_language(target_language)

    if not use_google_translate:
        if deepl_source is None or deepl_target is None:
            use_google_translate = True
        else:
            source_language = deepl_source
            target_language = deepl_target

    if source_language != target_language and use_google_translate:
        translation_client = TranslationServiceAsyncClient()

    async with MicrophoneStream(loop) as stream, websockets.connect(
        deepgram_url, extra_headers={"Authorization": f"Token {key}"}
    ) as ws, TaskGroup() as tg:
        tg.create_task(
            consumer(
                queue,
                source_language,
                target_language,
                translation_client,
                update_subtitles,
            )
        )

        tg.create_task(receiver(ws, queue))
        tg.create_task(sender(ws, stream.generator()))


def run_asyncio_loop(loop: AbstractEventLoop) -> None:
    set_event_loop(loop)
    loop.run_forever()


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="LiveTranslate: automatic simultaneous translation"
    )

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
        default="",
        type=str,
        help="Target language (default: ''). When empty translation is disabled and only transcript is displayed",
    )
    parser.add_argument(
        "-g",
        "--google-translate",
        action="store_true",
        default=False,
        help="Enable translation using Google Translate. By default, DeepL is used. Use this flag to enable it.",
    )

    args = parser.parse_args()

    app: QApplication
    update_subtitles: Callable[[str], None]

    app, update_subtitles = start_gui()

    target: str = args.target
    if not target:
        target = args.source

    asyncio_loop: AbstractEventLoop = new_event_loop()
    task: Task[None] = asyncio_loop.create_task(
        main(args.source, target, update_subtitles, args.google_translate)
    )

    def check_task():
        if not task.done():
            return

        try:
            task.result()  # This will re-raise any exception that occurred in the task.
        except Exception:
            QApplication.quit()
            raise

    thread: Thread = Thread(target=run_asyncio_loop, args=(asyncio_loop,), daemon=True)
    thread.start()

    timer: QTimer = QTimer()
    timer.timeout.connect(check_task)
    timer.start(1000)

    sys.exit(app.exec())
