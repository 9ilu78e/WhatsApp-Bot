from datetime import datetime
import re
import logging

logger = logging.getLogger("ReminderBot.LocalAI")


def chat_reply(user_text: str, max_tokens: int = 200):
    """A tiny local responder: handles greetings and simple echoes.
    This is synchronous and fast.
    """
    if not user_text:
        return "Hello!"
    t = user_text.strip().lower()
    if any(g in t for g in ["hi", "hello", "hey"]):
        return "Hello 👋 How can I help you with reminders today?"
    if "help" in t or "menu" in t or t == "?":
        return "Send messages like: 'remind me to call mom at 6pm' or 'remind me in 30 minutes to check oven'."
    # fallback: brief echo
    return f"I got: {user_text}"


def parse_reminder_with_ai(user_text: str):
    """Local parser that returns a list of dicts similar to the previous AI output.

    Recognizes patterns like:
      - remind me to <task> in N minutes/hours
      - remind me to <task> at HH:MM (am/pm optional)
      - remind me every day at HH:MM to <task>
      - simple greetings

    Returns [] when nothing matched.
    """
    if not user_text or not user_text.strip():
        return []
    text = user_text.strip()
    tl = text.lower()

    # greetings
    if tl in ("hi", "hello", "hey") or any(tl.startswith(g) for g in ["hi ", "hello "]):
        return [{"type": "greeting", "message": "Hello!"}]

    results = []

    # every day at 9am to take meds
    m = re.search(r"every day at (\d{1,2}(?::\d{2})?\s*(?:am|pm)?) (?:to )?(?P<task>.+)", tl)
    if m:
        time_part = m.group(1)
        task = m.group("task").strip()
        results.append({"type": "reminder", "task": task, "time": f"every day at {time_part}", "repeat": 365, "interval_seconds": 24 * 3600})
        return results

    # remind me to <task> in N minutes/hours
    m = re.search(r"remind me to (?P<task>.+?) in (?P<num>\d+) (?P<unit>minute|minutes|hour|hours)", tl)
    if m:
        task = m.group("task").strip()
        num = int(m.group("num"))
        unit = m.group("unit")
        if "minute" in unit:
            time_str = f"in {num} minutes"
            interval = num * 60
        else:
            time_str = f"in {num} hours"
            interval = num * 3600
        results.append({"type": "reminder", "task": task, "time": time_str, "repeat": 1, "interval_seconds": interval})
        return results

    # remind me to <task> at 6pm / at 18:00
    m = re.search(r"remind me to (?P<task>.+?) at (?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm)?)", tl)
    if m:
        task = m.group("task").strip()
        time_part = m.group("time").strip()
        results.append({"type": "reminder", "task": task, "time": time_part, "repeat": 1, "interval_seconds": 0})
        return results

    # plain: 'remind me to call mom tomorrow at 9am'
    m = re.search(r"remind me to (?P<task>.+?) tomorrow(?: at (?P<time>\d{1,2}(?::\d{2})?\s*(?:am|pm)?))?", tl)
    if m:
        task = m.group("task").strip()
        time_part = m.group("time") or "9:00"
        results.append({"type": "reminder", "task": task, "time": f"tomorrow at {time_part}", "repeat": 1, "interval_seconds": 0})
        return results

    # fallback: if message starts with 'remind' try to capture rest
    if tl.startswith("remind"):
        # try to extract the task after 'remind me to' or 'remind to'
        m = re.search(r"remind(?: me)?(?: to)? (?P<task>.+)", tl)
        if m:
            task = m.group("task").strip()
            # schedule in 1 minute as safe default
            results.append({"type": "reminder", "task": task, "time": "in 1 minutes", "repeat": 1, "interval_seconds": 60})
            return results

    return []
