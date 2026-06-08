from core.client import wa_client
from utils.logger import logger

def send_reminder(reminder):
    try:
        count = reminder.sent_count + 1
        prefix = f"Reminder #{count}" if reminder.repeat_count > 1 else "REMINDER"
        
        if reminder.check_done:
            message = f"Question: Have you {reminder.task.lower()} yet?\n\nReply *yes* or *no*"
        else:
            message = f"{reminder.task}"
            
        wa_client.send_message(reminder.user_phone, message)
        logger.info(f"Sent reminder to {reminder.user_phone}: {reminder.task}")
    except Exception as e:
        logger.error(f"Failed to send reminder: {e}")