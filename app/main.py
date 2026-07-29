from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import logging
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Care Sister Postpartum Bot")


@app.get("/")
async def root():
    return {"status": "Care Sister Bot is running"}


@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Handles Meta webhook verification (GET request)
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    logger.info(f"Verification attempt - Mode: {mode}, Token received: {token}")

    # Check if mode is 'subscribe' and token matches
    if mode == "subscribe" and token == settings.VERIFY_TOKEN:
        logger.info("Webhook verification successful!")
        return PlainTextResponse(content=challenge, status_code=200)
    
    logger.warning("Webhook verification failed - Invalid token or mode")
    raise HTTPException(status_code=403, detail="Verification failed")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Handles incoming messages from WhatsApp (POST request)
    """
    try:
        payload = await request.json()
        logger.info("Received webhook payload")
        # We will add message handling later
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error"}