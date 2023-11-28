import os

import aiohttp
from google.cloud.translate import TranslateTextResponse, TranslationServiceAsyncClient


async def translate_text_google(
    client: TranslationServiceAsyncClient,
    text: str,
    source_language: str,
    target_language: str,
) -> str:
    if not text:
        return ""

    location = "global"

    parent = f"projects/api-project-100069816556/locations/{location}"

    response: TranslateTextResponse = await client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",  # mime types: text/plain, text/html
            "source_language_code": source_language,
            "target_language_code": target_language,
        }
    )

    result: str = response.translations[0].translated_text.strip()
    return result


async def translate_text_deepl(
    text: str,
    source_lang: str,
    target_lang: str,
    context: str,
) -> str:
    """
    Asynchronously translate text using DeepL API and requests-async library.

    :param text: The text to be translated.
    :param source_language: The source language code.
    :param target_language: The target language code.
    :param context: Additional context for the translation.
    :return: The translated text as a string.
    """
    headers: dict[str, str] = {
        "Authorization": f'DeepL-Auth-Key {os.getenv("DEEPL_API_KEY")}',
        "Content-Type": "application/json",
    }

    payload: dict[str, str | list[str]] = {
        "text": [text],
        "source_lang": source_lang,
        "target_lang": target_lang,
        "context": context,
    }

    url: str = "https://api-free.deepl.com/v2/translate"

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            if not response.ok:
                print(response.text)
                return ""
            result = await response.json()

            translated_text: str = result["translations"][0]["text"]

    return translated_text


def deepl_language(language: str) -> str | None:
    deepl_supported: list[str] = [
        "BG",
        "CS",
        "DA",
        "DE",
        "EL",
        "EN",
        "EN-GB",
        "EN-US",
        "ES",
        "ET",
        "FI",
        "FR",
        "HU",
        "ID",
        "IT",
        "JA",
        "KO",
        "LT",
        "LV",
        "NB",
        "NL",
        "PL",
        "PT",
        "PT-BR",
        "PT-PT",
        "RO",
        "RU",
        "SK",
        "SL",
        "SV",
        "TR",
        "UK",
        "ZH",
    ]
    if (r := language.upper()) in deepl_supported:
        return r

    if (r := language.split("-")[0].upper()) in deepl_supported:
        return r

    return None
