import json
import os
import re
import time
from datetime import datetime

# Don't fetch the price list from GitHub at startup (slow/blocked on some networks)
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from litellm import completion

import config

SYSTEM_TEMPLATE = """You are {name}, a personal voice assistant.

Language rules:
- Reply in the language the user used. Tamil (தமிழ்) in Tamil script, English in English.
- If the user mixes Tamil and English (Tanglish), reply in natural Tamil with English words where a person would normally use them.
- Never switch languages unless the user does.

Style rules:
- Replies will be spoken aloud: short, natural, no markdown, no bullet lists, no emojis.
- Be warm and direct, like a helpful person, not a manual.

Current time: {now}

What you know about the user:
{facts}
"""


def build_system(facts: list[str]) -> str:
    facts_text = "\n".join(f"- {f}" for f in facts) or "- (nothing yet)"
    return SYSTEM_TEMPLATE.format(
        name=config.NAME,
        now=datetime.now().strftime("%A, %d %B %Y, %I:%M %p"),
        facts=facts_text,
    )


def _call(messages: list[dict]) -> str:
    """Try each model in turn; retry temporary errors (503, timeouts) first."""
    models = [m for m in (config.MODEL, config.FALLBACK_MODEL, config.FALLBACK_MODEL_2) if m]
    for model in models:
        for attempt in range(1, 4):  # up to 3 tries per model
            try:
                resp = completion(model=model, messages=messages, timeout=45)
                return resp.choices[0].message.content.strip()
            except Exception as e:
                msg = str(e)
                temporary = any(
                    k in msg for k in ("503", "UNAVAILABLE", "Timeout", "timed out", "429", "overloaded")
                )
                print(f"[brain] {model} try {attempt} failed: {msg[:120]}")
                if not temporary:
                    break  # bad key / bad model name: retrying won't help
                time.sleep(2 * attempt)
    return "Sorry, I can't reach my brain right now."


def reply(history: list[dict], facts: list[str]) -> str:
    messages = [{"role": "system", "content": build_system(facts)}] + history
    return _call(messages)


def extract_facts(history: list[dict], known: list[str]) -> list[str]:
    """Ask the model to pull lasting preferences/facts from a conversation."""
    if not history:
        return []
    transcript = "\n".join(f"{m['role']}: {m['content']}" for m in history)
    prompt = (
        "From this conversation, extract lasting facts or preferences about the "
        "user (name, habits, likes, aliases for devices, routines). Ignore "
        "one-off requests. Return ONLY a JSON array of short English strings. "
        "Return [] if nothing is worth remembering.\n\n"
        f"Already known: {json.dumps(known, ensure_ascii=False)}\n\n"
        f"Conversation:\n{transcript}"
    )
    raw = _call([{"role": "user", "content": prompt}])
    match = re.search(r"\[.*\]", raw, re.S)
    if not match:
        return []
    try:
        items = json.loads(match.group(0))
        return [str(i) for i in items if str(i).strip() and str(i) not in known]
    except json.JSONDecodeError:
        return []