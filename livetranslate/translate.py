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

    # Use the Pro API endpoint if USE_DEEPL_PRO is set to true
    use_pro = os.getenv("USE_DEEPL_PRO", "false").lower() == "true"
    url: str = "https://api.deepl.com/v2/translate" if use_pro else "https://api-free.deepl.com/v2/translate"

    async with aiohttp.ClientSession() as session, session.post(
        url, json=payload, headers=headers
    ) as response:
        if not response.ok:
            print(await response.text())
            return ""
        result = await response.json()

        translated_text: str = result["translations"][0]["text"]

    return translated_text


def deepl_language(language: str) -> str | None:
    # Common language code mappings
    language_map = {
        "CH": "ZH",  # Map CH (Chinese) to ZH (DeepL's code for Chinese)
        "CN": "ZH",  # Map CN to ZH
        "CZ": "CS",  # Map CZ (Czech) to CS
        "GR": "EL",  # Map GR (Greek) to EL
    }
    
    deepl_supported: list[str] = [
        "BG",  # Bulgarian
        "CS",  # Czech
        "DA",  # Danish
        "DE",  # German
        "EL",  # Greek
        "EN",  # English
        "EN-GB",  # British English
        "EN-US",  # American English
        "ES",  # Spanish
        "ET",  # Estonian
        "FI",  # Finnish
        "FR",  # French
        "HU",  # Hungarian
        "ID",  # Indonesian
        "IT",  # Italian
        "JA",  # Japanese
        "KO",  # Korean
        "LT",  # Lithuanian
        "LV",  # Latvian
        "NB",  # Norwegian
        "NL",  # Dutch
        "PL",  # Polish
        "PT",  # Portuguese
        "PT-BR",  # Brazilian Portuguese
        "PT-PT",  # European Portuguese
        "RO",  # Romanian
        "RU",  # Russian
        "SK",  # Slovak
        "SL",  # Slovenian
        "SV",  # Swedish
        "TR",  # Turkish
        "UK",  # Ukrainian
        "ZH",  # Chinese
    ]
    
    # Check for direct match after converting to uppercase
    code = language.upper()
    if code in deepl_supported:
        return code
    
    # Check if the code is in our mapping
    if code in language_map:
        return language_map[code]
    
    # Try to get the language part before the hyphen (e.g., "en-US" -> "en")
    base_code = code.split("-")[0]
    if base_code in deepl_supported:
        return base_code
    
    # Check if the base code is in our mapping
    if base_code in language_map:
        return language_map[base_code]
    
    # Return None if no match found
    return None
