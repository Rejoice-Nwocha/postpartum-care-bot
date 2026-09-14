from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import logging
from app.config import settings
from app.db import init_db, SessionLocal, MessageLog
from app.scheduler import start_scheduler
from app.state_machine import handle_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Care Sister Postpartum Bot")
scheduler = None


@app.on_event("startup")
async def startup():
    global scheduler
    init_db()
    scheduler = start_scheduler()
    logger.info(
        "Evolution configuration at startup: url=%s api_key=%s instance=%s",
        bool(settings.EVOLUTION_API_URL),
        bool(settings.EVOLUTION_API_KEY),
        bool(settings.EVOLUTION_INSTANCE),
    )
    logger.info("Care Sister database initialized")


@app.on_event("shutdown")
async def shutdown():
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Care Sister scheduler stopped")


@app.get("/")
async def root():
    return {
        "status": "Care Sister Bot is running",
        "whatsapp_provider": "Evolution API / Baileys",
        "evolution_configured": bool(settings.EVOLUTION_API_URL and settings.EVOLUTION_API_KEY and settings.EVOLUTION_INSTANCE),
    }


@app.get("/diagnostics")
async def diagnostics():
    return {
        "status": "ok",
        "evolution_configured": {
            "url_present": bool(settings.EVOLUTION_API_URL),
            "api_key_present": bool(settings.EVOLUTION_API_KEY),
            "instance_present": bool(settings.EVOLUTION_INSTANCE),
        },
        "scheduler_running": bool(scheduler and scheduler.running),
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token and token == settings.VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return {"status": "ok", "message": "Care Sister webhook endpoint is reachable"}


@app.post("/webhook")
async def receive_webhook(request: Request):
    # Keep the legacy path compatible with Evolution configurations that point
    # at /webhook instead of /webhook/evolution.
    logger.info("POST /webhook received; forwarding to Evolution handler")
    return await evolution_webhook(request)


def extract_evolution_message(payload: dict):
    data = payload.get("data") or {}
    key = data.get("key") or {}
    message = data.get("message") or {}

    remote_jid = key.get("remoteJid") or key.get("remoteJidAlt") or ""
    if not remote_jid or remote_jid.endswith("@g.us") or key.get("fromMe"):
        return None

    extended = message.get("extendedTextMessage") or {}
    image = message.get("imageMessage") or {}
    video = message.get("videoMessage") or {}
    text = (
        message.get("conversation")
        or extended.get("text")
        or image.get("caption")
        or video.get("caption")
        or ""
    ).strip()
    if not text:
        return None

    wa_id = remote_jid.split("@", 1)[0]
    first_name = (data.get("pushName") or key.get("pushName") or "Mama").strip() or "Mama"
    message_id = key.get("id") or ""
    return wa_id, text, first_name, message_id


@app.post("/webhook/evolution")
async def evolution_webhook(request: Request):
    try:
        payload = await request.json()
        event = str(payload.get("event") or "").strip().upper().replace(".", "_")
        logger.info("Evolution webhook received: event=%s", event or "unknown")

        if event and event not in {"MESSAGES_UPSERT", "MESSAGES_UPSERTED"}:
            logger.info("Ignoring Evolution event: %s", event)
            return {"status": "ignored", "event": event}

        extracted = extract_evolution_message(payload)
        if not extracted:
            logger.info("Evolution payload contained no user text message")
            return {"status": "ignored"}

        wa_id, text, first_name, message_id = extracted
        logger.info("Processing inbound WhatsApp message: wa_id=%s message_id=%s", wa_id, message_id or "none")

        db = SessionLocal()
        try:
            if message_id:
                duplicate = db.query(MessageLog).filter(
                    MessageLog.wa_id == wa_id,
                    MessageLog.direction == "in",
                    MessageLog.body.startswith(f"[evolution:{message_id}]")
                ).first()
                if duplicate:
                    logger.info("Duplicate Evolution message ignored: %s", message_id)
                    return {"status": "duplicate"}

            logged_body = f"[evolution:{message_id}] {text}" if message_id else text
            db.add(MessageLog(wa_id=wa_id, direction="in", body=logged_body))
            db.commit()
            await handle_message(db, wa_id, text, first_name)
        finally:
            db.close()

        logger.info("Inbound message handled successfully: wa_id=%s", wa_id)
        return {"status": "ok"}
    except Exception:
        logger.exception("Error processing Evolution webhook")
        return {"status": "error"}
