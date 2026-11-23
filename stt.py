"""Microphone listening: record one utterance, then transcribe (Tamil/English)."""
import queue
from collections import deque

import numpy as np
import sounddevice as sd

import config

SAMPLE_RATE = 16000
BLOCK = 480  # 30 ms
BLOCK_S = BLOCK / SAMPLE_RATE
MIN_THRESHOLD = 0.008  # never trigger below this volume
CALIBRATE_BLOCKS = 15  # ~0.45 s of room noise
PRE_ROLL_BLOCKS = 10  # keep 0.3 s before speech starts
WAIT_FOR_SPEECH_S = 8.0
MAX_UTTERANCE_S = 20.0
MIN_UTTERANCE_S = 0.4

_model = None


def _rms(block: np.ndarray) -> float:
    return float(np.sqrt(np.mean(block**2)))


def listen():
    """Block until the user speaks and then pauses. Returns float32 audio or None."""
    q: queue.Queue = queue.Queue()

    def callback(indata, frames, time_info, status):
        q.put(indata[:, 0].copy())

    end_silence_blocks = int(config.END_SILENCE_S / BLOCK_S)
    max_wait_blocks = int(WAIT_FOR_SPEECH_S / BLOCK_S)
    max_blocks = int(MAX_UTTERANCE_S / BLOCK_S)

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocksize=BLOCK,
        device=config.MIC_DEVICE,
        callback=callback,
    ):
        # Measure room noise so the speech threshold adapts to your mic/room
        noise = np.mean([_rms(q.get()) for _ in range(CALIBRATE_BLOCKS)])
        threshold = max(noise * 3.0, MIN_THRESHOLD)

        pre = deque(maxlen=PRE_ROLL_BLOCKS)
        frames: list = []
        speaking = False
        silent = 0
        waited = 0

        while True:
            block = q.get()
            loud = _rms(block) > threshold
            if not speaking:
                pre.append(block)
                if loud:
                    speaking = True
                    frames = list(pre)
                else:
                    waited += 1
                    if waited > max_wait_blocks:
                        return None
            else:
                frames.append(block)
                silent = 0 if loud else silent + 1
                if silent >= end_silence_blocks or len(frames) >= max_blocks:
                    break

    audio = np.concatenate(frames)
    if len(audio) / SAMPLE_RATE < MIN_UTTERANCE_S:
        return None
    return audio


def _get_model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        print(f"Loading speech model '{config.WHISPER_MODEL}' "
              "(first run downloads it, please wait)...")
        _model = WhisperModel(
            config.WHISPER_MODEL, device="cpu", compute_type=config.WHISPER_COMPUTE
        )
    return _model


def preload():
    _get_model()


def transcribe(audio: np.ndarray):
    """Returns (text, language) where language is 'ta' or 'en'."""
    model = _get_model()

    # Limit detection to Tamil vs English: far fewer wrong-language mistakes
    lang = None
    try:
        _, _, probs = model.detect_language(audio)
        p = dict(probs)
        lang = "ta" if p.get("ta", 0) > p.get("en", 0) else "en"
    except Exception:
        pass

    segments, info = model.transcribe(
        audio,
        language=lang,
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    text = " ".join(s.text.strip() for s in segments).strip()
    return text, (lang or info.language)


def listen_and_transcribe():
    """One full turn of hearing. Returns (text, lang) or (None, None)."""
    audio = listen()
    if audio is None:
        return None, None
    text, lang = transcribe(audio)
    if len(text) < 2:
        return None, None
    return text, lang
