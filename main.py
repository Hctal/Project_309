import sys

import brain
import config
import tts
from memory import Memory

# Make Tamil print correctly in the Windows terminal
sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

TEXT_MODE = "--text" in sys.argv
EXIT_WORDS = {"bye", "goodbye", "exit", "quit", "good bye", "பை", "வெளியேறு"}
HELP_TEXT = "Commands: /facts | /mute | /unmute | /quit"


def say(text: str):
    print(f"{config.NAME}: {text}\n")
    tts.speak(text)


def get_user_input() -> str | None:
    """Return the next thing the user said/typed. None = nothing heard."""
    if TEXT_MODE:
        return input("You: ").strip()

    import stt

    print("Listening...", end="\r", flush=True)
    text, lang = stt.listen_and_transcribe()
    print(" " * 20, end="\r")
    if not text:
        return None
    print(f"You ({lang}): {text}")
    return text


def main():
    mem = Memory(config.DB_PATH)
    session = []  # messages from this run only (used for fact extraction)

    if TEXT_MODE:
        print(HELP_TEXT)
    else:
        import stt

        stt.preload()
        print("Voice mode: just talk. Say 'bye' or press Ctrl+C to exit.\n")
    say("வணக்கம்! நான்  " + config.NAME + ". How can I help you?")

    while True:
        try:
            text = get_user_input()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue

        cleaned = text.lower().strip(" .!?,")
        if cleaned in EXIT_WORDS or text == "/quit":
            break
        if text == "/mute":
            config.TTS_ENABLED = False
            print("(muted)")
            continue
        if text == "/unmute":
            config.TTS_ENABLED = True
            print("(unmuted)")
            continue
        if text == "/facts":
            for f in mem.all_facts() or ["(nothing learned yet)"]:
                print(" -", f)
            continue

        mem.log_command(text)
        mem.add_message("user", text)
        session.append({"role": "user", "content": text})

        history = mem.recent_messages(config.HISTORY_TURNS)
        answer = brain.reply(history, mem.all_facts())

        mem.add_message("assistant", answer)
        session.append({"role": "assistant", "content": answer})
        say(answer)  # it finishes speaking before it listens again

    # On exit, learn lasting facts from this conversation
    print("\nSaving what I learned...")
    for fact in brain.extract_facts(session, mem.all_facts()):
        mem.add_fact(fact)
        print(" + learned:", fact)
    print("Bye!")


if __name__ == "__main__":
    main()
