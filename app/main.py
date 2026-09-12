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


@app.get("/")
async def root():
    return {"status": "Care Sister Bot is running", "whatsapp_provider": "evolution-test"}


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

    # Ignore messages sent by the connected WhatsApp account itself.
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

        event = str(payload.get("event") or "").upper()
        if event and event not in {"MESSAGES_UPSERT", "MESSAGES_UPSERTED"}:
            return {"status": "ignored", "event": event}

        extracted = extract_evolution_message(payload)
        if not extracted:
            return {"status": "ignored"}

        wa_id, text, first_name = extracted
        logger.info("Evolution message received from %s", wa_id)

        db = SessionLocal()
        try:
            await handle_message(db, wa_id, text, first_name)
        finally:
            db.close()

        return {"status": "ok"}
    except Exception as e:
        logger.exception("Error processing Evolution webhook: %s", e)
        # Return 200 so a transient bot-side error does not cause an uncontrolled
        # webhook retry storm while we are testing.
        return {"status": "error"}
