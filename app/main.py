from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import logging
from app.config import settings
from app.db import init_db, SessionLocal
from app.state_machine import handle_message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Care Sister Postpartum Bot")


@app.on_event("startup")
async def startup():
    init_db()
    logger.info("Care Sister database initialized")
    logger.info(
        "Evolution configuration at startup: url=%s api_key=%s instance=%s",
        bool(settings.EVOLUTION_API_URL),
        bool(settings.EVOLUTION_API_KEY),
        bool(settings.EVOLUTION_INSTANCE),
    )


@app.get("/")
async def root():
    return {"status": "Care Sister Bot is running", "whatsapp_provider": "evolution-test"}


@app.get("/diagnostics")
async def diagnostics():
    """Safe configuration diagnostic; never returns secret values."""
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
    """Legacy Meta webhook verification; kept for later production integration."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)

    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """Legacy Meta webhook endpoint; retained while Evolution is used for testing."""
    try:
        payload = await request.json()
        logger.info("Received legacy webhook payload")
        return {"status": "ok"}
    except Exception as e:
        logger.error("Error processing legacy webhook: %s", e)
        return {"status": "error"}


def extract_evolution_message(payload: dict):
    """Extract the basic sender/message fields from an Evolution MESSAGES_UPSERT payload."""
    data = payload.get("data") or {}
    key = data.get("key") or {}
    message = data.get("message") or {}

    remote_jid = key.get("remoteJid") or ""
    if not remote_jid or remote_jid.endswith("@g.us"):
        return None

    if key.get("fromMe"):
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
    first_name = data.get("pushName") or "Mama"
    return wa_id, text, first_name


@app.post("/webhook/evolution")
async def evolution_webhook(request: Request):
    """Receive Evolution API MESSAGES_UPSERT events and run Care Sister."""
    try:
        payload = await request.json()
        logger.info("Evolution webhook received: event=%s keys=%s", payload.get("event"), list(payload.keys()))
        data = payload.get("data") or {}
        key = data.get("key") or {}
        message = data.get("message") or {}
        logger.info(
            "Evolution payload details: remoteJid=%s fromMe=%s messageKeys=%s",
            key.get("remoteJid"), key.get("fromMe"), list(message.keys())
        )

        # Evolution v2 uses a dotted event name such as "messages.upsert".
        # Normalize punctuation/case so both dotted and underscored variants work.
        event = str(payload.get("event") or "").strip().upper().replace(".", "_")
        if event and event not in {"MESSAGES_UPSERT", "MESSAGES_UPSERTED"}:
            logger.info("Ignoring Evolution event: %s", event)
            return {"status": "ignored", "event": event}

        extracted = extract_evolution_message(payload)
        if not extracted:
            logger.info("Evolution webhook ignored: no inbound text message extracted")
            return {"status": "ignored"}

        wa_id, text, first_name = extracted
        logger.info("Evolution message extracted: sender=%s first_name=%s text=%r", wa_id, first_name, text)

        db = SessionLocal()
        try:
            await handle_message(db, wa_id, text, first_name)
            logger.info("Care Sister handled message successfully for %s", wa_id)
        finally:
            db.close()

        return {"status": "ok"}
    except Exception as e:
        logger.exception("Error processing Evolution webhook: %s", e)
        return {"status": "error"}
