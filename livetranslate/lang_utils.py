def last_words(text: str, n: int) -> str:
    last_words: str = " ".join(text.split(" ")[-n:])

    return last_words


def merge(prev_translation: str, tranlsation: str) -> tuple[str, bool]:
    for i in range(len(prev_translation)):
        if tranlsation.startswith(prev_translation[i:]):
            return prev_translation + tranlsation[len(prev_translation) - i :], True

    return tranlsation, False
