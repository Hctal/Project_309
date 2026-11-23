"""Tries several Gemini models and shows which are fast and working for you."""
import os
import sys
import time

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
from litellm import completion

load_dotenv()

CANDIDATES = [
    "gemini/gemini-2.5-flash",
    "gemini/gemini-3.5-flash",
    "gemini/gemini-3.6-flash",
    "gemini/gemini-3.7-flash",
    "gemini/gemini-2.5-flash-lite",
    "gemini/gemini-3.5-flash-lite",
]

PROMPT = "Reply in Tamil in one short sentence: how are you today?"

print(f"{'model':35} {'result':8} {'time':>6}  reply")
for model in CANDIDATES:
    start = time.time()
    try:
        r = completion(
            model=model,
            messages=[{"role": "user", "content": PROMPT}],
            timeout=40,
        )
        text = r.choices[0].message.content.strip().replace("\n", " ")
        print(f"{model:35} {'OK':8} {time.time() - start:5.1f}s  {text[:60]}")
    except Exception as e:
        reason = "503" if "503" in str(e) else "timeout" if "imeout" in str(e) else "error"
        print(f"{model:35} {'FAIL':8} {time.time() - start:5.1f}s  {reason}: {str(e)[:50]!r}")