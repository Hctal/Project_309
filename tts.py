import asyncio
import os
import re
import tempfile

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import edge_tts
import pygame

import config

TAMIL = re.compile(r"[\u0B80-\u0BFF]")
LATIN = re.compile(r"[A-Za-z]")
VOICES = {"ta": config.TAMIL_VOICE, "en": config.ENGLISH_VOICE}

_mixer_ready = False


def clean(text: str) -> str:
    """Remove things that sound bad when read aloud."""
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[*_`#>~]+", "", text)
    return text.strip()


def split_by_language(text: str) -> list[tuple[str, str]]:
    """Split text into [(lang, text)] runs so each uses the right voice."""
    runs: list[list] = []
    for word in text.split():
        if TAMIL.search(word):
            lang = "ta"
        elif LATIN.search(word):
            lang = "en"
        else:  # numbers / punctuation inherit the previous language
            lang = runs[-1][0] if runs else "en"
        if runs and runs[-1][0] == lang:
            runs[-1][1].append(word)
        else:
            runs.append([lang, [word]])

    # A lone English word inside Tamil stays in the Tamil voice (less choppy)
    merged: list[list] = []
    for lang, words in runs:
        if merged and merged[-1][0] == "ta" and lang == "en" and len(words) == 1:
            merged[-1][1].extend(words)
        elif merged and merged[-1][0] == lang:
            merged[-1][1].extend(words)
        else:
            merged.append([lang, list(words)])
    return [(lang, " ".join(words)) for lang, words in merged]


async def _synthesize(segments, folder):
    async def one(i, lang, text):
        path = os.path.join(folder, f"{i}.mp3")
        await edge_tts.Communicate(text, VOICES[lang], rate=config.TTS_RATE).save(path)
        return path

    # Generate all segments in parallel, keep order
    return await asyncio.gather(*(one(i, l, t) for i, (l, t) in enumerate(segments)))


def _play(paths):
    global _mixer_ready
    if not _mixer_ready:
        pygame.mixer.init()
        _mixer_ready = True
    try:
        for path in paths:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(50)
    except KeyboardInterrupt:  # Ctrl+C skips the speech
        pygame.mixer.music.stop()
    finally:
        pygame.mixer.music.unload()  # release the file so Windows can delete it


def speak(text: str):
    if not config.TTS_ENABLED:
        return
    text = clean(text)
    if not text:
        return
    segments = split_by_language(text)
    with tempfile.TemporaryDirectory() as folder:
        try:
            paths = asyncio.run(_synthesize(segments, folder))
        except Exception as e:  # offline, service change...
            print(f"[tts] failed: {e}")
            return
        _play(paths)
