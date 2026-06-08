from datetime import datetime, timedelta
from dateutil import parser as date_parser
import pytz
from core.local_ai import parse_reminder_with_ai
import logging
import re

logger = logging.getLogger("ReminderBot.Parser")
tz = pytz.timezone("Africa/Lagos")

def parse_reminder_flexible(text: str, phone: str):
    if not text or not text.strip():
        return None

    ai_parsed = parse_reminder_with_ai(text)
    if not ai_parsed:
        return None

    results = []
    now = datetime.now(tz)
    for item in ai_parsed:
        if isinstance(item, str):
            continue
        if item.get("type") == "greeting":
            results.append({"type": "greeting", "message": item.get("message")})
            continue

        task = item.get("task")
        time_str = item.get("time")
        repeat = int(item.get("repeat", 1))
        interval_seconds = int(item.get("interval_seconds", 0))
        try:
            dt = now
            if time_str:

                if "every day" in time_str.lower():
                    dt = now + timedelta(days=1)
                    if repeat < 1:
                        repeat = 1
                    if interval_seconds < 1:
                        interval_seconds = 24 * 3600

                else:
                    m = re.match(r"in (\d+) (minute|minutes|hour|hours)", time_str)
                    if m:
                        val, unit = m.groups()
                        val = int(val)
                        if "minute" in unit:
                            dt += timedelta(minutes=val)
                        elif "hour" in unit:
                            dt += timedelta(hours=val)
                    else:
                        dt = date_parser.parse(time_str, default=now)
                        if dt.tzinfo is None:
                            dt = tz.localize(dt)
                        if dt < now:
                            dt += timedelta(days=1)
        except Exception:
            logger.warning(f"Unparseable time: {time_str}")
            continue

        results.append({
            "type": "reminder",
            "task": task,
            "remind_time": dt,
            "repeat_count": repeat,
            "interval_seconds": interval_seconds,
            "interval_minutes": interval_seconds // 60
        })

    return results if results else None
