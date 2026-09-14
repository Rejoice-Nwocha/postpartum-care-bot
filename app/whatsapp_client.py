import logging
from urllib.parse import urlsplit

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def _send_request(path: str, payload: dict):
    if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE:
        logger.warning("Evolution API is not configured; message was not sent")
        return {"status": "not_configured"}

    base_url = settings.EVOLUTION_API_URL.rstrip("/")
    url = f"{base_url}{path}"
    parsed = urlsplit(base_url)
    safe_host = parsed.netloc or parsed.path
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }

    last_error = None
    for attempt in range(1, 3):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=8.0)) as client:
                response = await client.post(url, json=payload, headers=headers)
                if response.status_code >= 400:
                    logger.error("Evolution API returned HTTP %s from %s", response.status_code, safe_host)
                response.raise_for_status()
                try:
                    return response.json()
                except ValueError:
                    return {"status": "ok", "raw_response": response.text[:500]}
        except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
            last_error = exc
            logger.warning("Evolution outbound attempt %s failed for %s: %s", attempt, safe_host, type(exc).__name__)

    logger.error("Evolution outbound delivery failed after retries for %s", safe_host)
    raise last_error


async def send_text(to_wa_id: str, body: str):
    if not to_wa_id or not body:
        raise ValueError("Recipient and message body are required")

    payload = {
        "number": to_wa_id,
        "text": body,
    }
    return await _send_request(
        f"/message/sendText/{settings.EVOLUTION_INSTANCE}",
        payload,
    )


async def send_buttons(to_wa_id: str, body: str, buttons: list):
    # Numbered text is deliberately provider-independent and works even when
    # interactive WhatsApp message rendering is unavailable.
    options = "\n".join(f"{i + 1}. {title}" for i, title in enumerate(buttons))
    return await send_text(to_wa_id, f"{body}\n\n{options}\n\nReply with the number of your choice.")
