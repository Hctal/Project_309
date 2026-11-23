import os

os.environ.setdefault("HF_HUB_DISABLE_XET", "1")  # more reliable model downloads
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "gemini/gemini-2.5-flash")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "").strip()
FALLBACK_MODEL_2 = os.getenv("FALLBACK_MODEL_2", "").strip()
NAME = os.getenv("ASSISTANT_NAME", "Nila")
DB_PATH = "data/assistant.db"
HISTORY_TURNS = 20  # recent messages sent to the model each turn

# --- Voice output ---
TTS_ENABLED = os.getenv("TTS_ENABLED", "1") == "1"
TAMIL_VOICE = os.getenv("TAMIL_VOICE", "ta-IN-PallaviNeural")
ENGLISH_VOICE = os.getenv("ENGLISH_VOICE", "en-IN-NeerjaNeural")
TTS_RATE = os.getenv("TTS_RATE", "+0%")  # e.g. "+10%" faster, "-10%" slower

# --- Voice input ---
STT_ENABLED = os.getenv("STT_ENABLED", "1") == "1"
# large-v3-turbo = best Tamil (~1.6 GB download). Use "small" on a weak PC.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3-turbo")
MIC_DEVICE = os.getenv("MIC_DEVICE", "").strip()  # blank = Windows default mic
SILENCE_SECONDS = float(os.getenv("SILENCE_SECONDS", "1.0"))  # pause that ends your sentence
MIN_THRESHOLD = float(os.getenv("MIN_THRESHOLD", "0.008"))  # raise if noisy room
MAX_RECORD_SECONDS = 30
WAIT_FOR_SPEECH_SECONDS = 6

# --- Voice input ---
# Bigger = better Tamil but slower on CPU. Try "small" if it feels too slow.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3-turbo")
WHISPER_COMPUTE = os.getenv("WHISPER_COMPUTE", "int8")
MIC_DEVICE = os.getenv("MIC_DEVICE", "").strip() or None  # None = default mic
END_SILENCE_S = float(os.getenv("END_SILENCE_S", "1.0"))  # pause that ends your turn