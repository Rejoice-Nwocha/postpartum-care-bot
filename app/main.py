from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import logging
from app.config import settings
from app.db import init_db, SessionLocal, MessageLog
from app.state_machine import handle_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Care Sister Postpartum Bot")


@app.on_event("startup")
async def startup():
    init_db()
    logger.info(
        "Evolution configuration at startup: url=%s api_key=%s instance=%s",
        bool(settings.EVOLUTION_API_URL),
        bool(settings.EVOLUTION_API_KEY),
        bool(settings.EVOLUTION_INSTANCE),
    )
    logger.info("Care Sister database initialized")


@app.get("/")
async def root():
    return {
        "status": "Care Sister Bot is running",
        "whatsapp_provider": "Evolution API / Baileys",
        "evolution_configured": bool(
            settings.EVOLUTION_API_URL
            and settings.EVOLUTION_API_KEY
            and settings.EVOLUTION_INSTANCE
        ),
    }


@app.get("/diagnostics")
async def diagnostics():
    """Safe configuration check; never returns secret values."""
    return {
        "status": "ok",
        "evolution_configured": {
            "url_present": bool(settings.EVOLUTION_API_URL),
            "api_key_present": bool(settings.EVOLUTION_API_KEY),
            "instance_present": bool(settings.EVOLUTION_INSTANCE),
        },
    }


@app.get("/webhook")
async def verify_webhook(request: Request):
    """Legacy Meta webhook verification; retained for later integration."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Legacy Meta endpoint; retained for later integration."""
    try:
        await request.json()
        logger.info("Received legacy webhook payload")
        return {"status": "ok"}
    except Exception:
        logger.exception("Error processing legacy webhook")
        return {"status": "error"}


def extract_evolution_message(payload: dict):
    """Extract inbound one-to-one text from an Evolution MESSAGES_UPSERT payload."""
    data = payload.get("data") or {}
    key = data.get("key") or {}
    message = data.get("message") or {}
    remote_jid = key.get("remoteJid") or ""

    # Ignore groups and messages sent by the bot itself.
    if not remote_jid or remote_jid.endswith("@g.us") or key.get("fromMe"):
        return None

    text = (
        message.get("conversation")
        or (message.get("extendedTextMessage") or {}).get("text")
        or (message.get("imageMessage") or {}).get("caption")
        or (message.get("videoMessage") or {}).get("caption")
        or ""
    ).strip()
    if not text:
        return None

    wa_id = remote_jid.split("@", 1)[0]
    first_name = (data.get("pushName") or "Mama").strip() or "Mama"
    message_id = key.get("id") or ""
    return wa_id, text, first_name, message_id


@app.post("/webhook/evolution")
async def evolution_webhook(request: Request):
    """Receive Evolution API MESSAGES_UPSERT events and run Care Sister."""
    try:
        payload = await request.json()
        event = str(payload.get("event") or "").strip().upper().replace(".", "_")
        if event and event not in {"MESSAGES_UPSERT", "MESSAGES_UPSERTED"}:
            return {"status": "ignored", "event": event}

        extracted = extract_evolution_message(payload)
        if not extracted:
            return {"status": "ignored"}

        wa_id, text, first_name, message_id = extracted
        db = SessionLocal()
        try:
            # Evolution can retry webhook delivery. A WhatsApp message id is
            # the stable dedupe key when it is supplied.
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

        return {"status": "ok"}
    except Exception:
        logger.exception("Error processing Evolution webhook")
        return {"status": "error"}
