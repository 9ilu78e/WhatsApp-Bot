from core.client import wa_client
from services.reminder_service import add_reminder, list_reminders, delete_reminder
from utils.parser import parse_reminder_flexible
from utils.formatter import format_reminders
from utils.logger import logger
from config.settings import ALLOWED_USERS
from core.local_ai import chat_reply
from utils.greeting import get_greeting
from utils.help import get_help
from models.reminder import Reminder
import asyncio
from datetime import datetime

async def handle_incoming_message(message: dict, metadata: dict):
    from_number = message.get("from", "")
    message_type = message.get("type", "text")
    message_id = message.get("id", "")
    if message_type != "text":
        return
    text = message.get("text", {}).get("body", "").strip()
    if not text:
        return
    logger.info(f"Received message from {from_number}: {text}")
    if from_number not in ALLOWED_USERS:
        wa_client.send_message(from_number, "You are not authorized to use this bot.")
        return
    await process_text_message(from_number, text, message_id)

async def process_text_message(from_number: str, text: str, message_id: str):
    try:
        text_lower = text.lower().strip()

        if text_lower in ["help", "menu", "?", "assist", "guide me"]:
            wa_client.send_message(from_number, get_help())
            return

        logger.info(f"Parsing reminders from message: {text}")
        parsed = parse_reminder_flexible(text, from_number)
        logger.info(f"Parsed reminders: {parsed}")

        if parsed:
            for item in parsed:
                if item.get("type") == "greeting":
                    wa_client.send_message(from_number, get_greeting())
                    return

            for item in parsed:
                if item.get("type") == "reminder":
                    reminder_data = item
                    remind_time = reminder_data["remind_time"]
                    if isinstance(remind_time, str):
                        remind_time = datetime.fromisoformat(remind_time)
                    reminder_obj = Reminder(
                        user_phone=from_number,
                        task=reminder_data["task"],
                        remind_time=remind_time,
                        repeat_count=reminder_data.get("repeat_count", 1),
                        interval_seconds=reminder_data.get("interval_seconds", 0)
                    )
                    add_reminder(reminder_obj)
                    wa_client.send_message(
                        from_number,
                        f"✅ Reminder set successfully!\n\n"
                        f"📌 Task: {reminder_obj.task}\n"
                        f"⏰ Start Time: {reminder_obj.remind_time.strftime('%I:%M %p')}\n"
                        f"🔁 Repeat: {reminder_obj.repeat_count} time(s)\n"
                        f"⏱ Interval: {reminder_obj.interval_seconds // 60} minute(s)"
                    )

            return

        if "my reminders" in text_lower or "list reminders" in text_lower:
            reminders = list_reminders(from_number)
            if not reminders:
                wa_client.send_message(from_number, "No reminders set.")
                return
            formatted = format_reminders(reminders)
            wa_client.send_message(from_number, formatted)
            return

        if text_lower.startswith("delete reminder"):
            parts = text_lower.split()
            if len(parts) >= 3:
                try:
                    index = int(parts[2]) - 1
                    delete_reminder(from_number, index)
                    wa_client.send_message(from_number, "✅ Reminder deleted.")
                    return
                except (ValueError, IndexError):
                    wa_client.send_message(from_number, "Invalid reminder number.")
                    return
            wa_client.send_message(from_number, "Invalid delete reminder command.")
            return

        # Send immediate acknowledgement and perform AI reply in background
        wa_client.send_message(from_number, "Got it — I'm processing your message and will reply shortly.")

        async def _background_ai_reply(to, user_text):
            try:
                # Run blocking AI call in a thread to avoid blocking the event loop
                reply = await asyncio.to_thread(chat_reply, user_text, 200)
                if reply is None:
                    # fallback: echo user message so user gets a helpful reply
                    wa_client.send_message(to, f"I couldn't reach AI — you said: {user_text}")
                else:
                    wa_client.send_message(to, reply)
            except Exception as e:
                logger.exception(f"Background AI reply failed: {e}")
                try:
                    wa_client.send_message(to, "AI unavailable. Try later....")
                except Exception:
                    pass

        asyncio.create_task(_background_ai_reply(from_number, text))

    except Exception as e:
        logger.exception(f"Error in process_text_message: {e}")
        wa_client.send_message(from_number, "Sorry, something went wrong processing your message.")
