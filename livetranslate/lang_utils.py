def last_words(text: str, n: int) -> str:
    last_words: str = " ".join(text.split(" ")[-n:])

    return last_words


def merge(prev_translation: str, tranlsation: str) -> tuple[str, bool]:
    for i in range(len(prev_translation)):
        if tranlsation.startswith(prev_translation[i:]):
            return prev_translation + tranlsation[len(prev_translation) - i :], True

    return tranlsation, False


def last_sentence(text: str) -> str:
    text = text.strip()

    if ". " in text:
        text = ". ".join(text.split(". ")[-1:])

    if "? " in text:
        text = ". ".join(text.split("? ")[-1:])

    if "! " in text:
        text = ". ".join(text.split("! ")[-1:])

    return text
