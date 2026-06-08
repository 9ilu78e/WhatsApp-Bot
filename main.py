import os
import uvicorn
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
from dotenv import load_dotenv
from handlers.message_handler import handle_incoming_message
from core.scheduler import start_scheduler
from handlers.callback_handlers import register_callback_handlers
from services.reminder_service import load_reminders
from services.notifier import send_reminder
from utils.logger import logger
from pywa import WhatsApp
from datetime import datetime
import pytz

load_dotenv()

app = FastAPI(title="WhatsApp Reminder Bot")
tz = pytz.timezone("Africa/Lagos")

wa = WhatsApp(
    phone_id=os.getenv("WHATSAPP_PHONE_ID"),
    token=os.getenv("WHATSAPP_TOKEN"),
    verify_token=os.getenv("VERIFY_TOKEN"),
    server=app
)

register_callback_handlers(wa)

async def reminder_loop():
    while True:
        now = datetime.now(tz)
        reminders = load_reminders()
        for r in reminders:
            if r.remind_time <= now and r.sent_count < r.repeat_count:
                send_reminder(r)
        await asyncio.sleep(60)

@app.on_event("startup")
def on_startup():
    start_scheduler()
    asyncio.create_task(reminder_loop())

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = request.query_params

    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == os.getenv("VERIFY_TOKEN"):
        return PlainTextResponse(str(challenge), media_type="text/plain")

    return PlainTextResponse("Verification failed", status_code=403)

@app.post("/webhook")
async def handle_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid json"}, status_code=400)

    # Log the incoming payload for debugging
    try:
        logger.info(f"🔥 WEBHOOK RECEIVED: {data}")
    except Exception:
        pass

    # Safe parsing of the WhatsApp webhook structure
    if data.get("object") == "whatsapp_business_account":
        entries = data.get("entry", []) or []
        for entry in entries:
            changes = entry.get("changes", []) or []
            for change in changes:
                value = change.get("value") or {}
                messages = value.get("messages") or []
                statuses = value.get("statuses") or []

                if messages:
                    for message in messages:
                        # log basic info
                        from_number = message.get("from")
                        text = message.get("text", {}).get("body") if message.get("type") == "text" else None
                        logger.info(f"📩 From: {from_number} | Type: {message.get('type')} | Text: {text}")
                        # process message using existing handler (await to ensure execution)
                        try:
                            await handle_incoming_message(message, value)
                        except Exception as e:
                            logger.exception(f"Failed to process incoming message: {e}")

                if statuses:
                    for status in statuses:
                        logger.info(f"Message status: {status}")

    return {"status": "ok"}

@app.get("/health")
async def health_check():
    return {"status": "running"}

@app.get("/ping")
async def ping():
    return PlainTextResponse("OK")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
