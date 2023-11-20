from google.cloud.translate import TranslateTextResponse, TranslationServiceAsyncClient


def last_words(text: str, n: int) -> str:
    last_words: str = " ".join(text.split(" ")[-n:])

    return last_words


async def translate_text(text: str) -> str:
    if not text:
        return ""

    client = TranslationServiceAsyncClient()

    location = "global"

    parent = f"projects/api-project-100069816556/locations/{location}"

    response: TranslateTextResponse = await client.translate_text(
        request={
            "parent": parent,
            "contents": [last_words(text, 30)],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "source_language_code": "ru-RU",
            "target_language_code": "pt-BR",
        }
    )

    return last_words(response.translations[0].translated_text, 10).strip()
