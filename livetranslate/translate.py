from google.cloud.translate import TranslateTextResponse, TranslationServiceAsyncClient

from livetranslate.lang_utils import last_sentence


async def translate_text(text: str, source_language: str, target_language: str) -> str:
    if not text:
        return ""

    client = TranslationServiceAsyncClient()

    location = "global"

    parent = f"projects/api-project-100069816556/locations/{location}"

    response: TranslateTextResponse = await client.translate_text(
        request={
            "parent": parent,
            # "contents": [last_words(text, 30)],
            "contents": [last_sentence(text)],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "source_language_code": source_language,
            "target_language_code": target_language,
        }
    )

    result: str = response.translations[0].translated_text.strip()
    return result
    # return last_words(result, 15).strip()
