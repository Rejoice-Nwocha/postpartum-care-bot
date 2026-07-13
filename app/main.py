from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
import logging

from app.config import settings
from app.db import init_db, get_db
from app import whatsapp_client, safety_scanner, state_machine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Care Sister Postpartum Bot")


@app.on_event('startup')
async def startup():
    init_db()
    logger.info('Care Sister Bot started.')


@app.get('/webhook')
async def verify_webhook(request: Request):
    params = request.query_params
    if params.get('hub.mode') == 'subscribe' and params.get('hub.verify_token') == settings.VERIFY_TOKEN:
        return PlainTextResponse(params.get('hub.challenge'))
    raise HTTPException(403, 'Invalid token')


@app.post('/webhook')
async def webhook(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
        # Basic handling - expand later
        logger.info('Received webhook')
    except Exception as e:
        logger.error(e)
    return {'status': 'ok'}
