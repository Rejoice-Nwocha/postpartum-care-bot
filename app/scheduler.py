import logging
from datetime import date, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.db import SessionLocal, Mother
from app.whatsapp_client import send_text

logger = logging.getLogger(__name__)
CHECKIN_DAYS = (3, 7, 14)


async def send_checkin(wa_id: str, day: int):
    message = (
        f"Day {day} check-in, Mama.\n\n"
        "How are you feeling today? You can tell me about your recovery, emotions, "
        "body, breastfeeding, baby, food, sleep or anything else on your mind."
    )
    await send_text(wa_id, message)


async def run_checkins():
    """Send due check-ins once, recording them before sending to avoid duplicates."""
    db = SessionLocal()
    try:
        today = date.today()
        mothers = db.query(Mother).filter(Mother.delivery_date.isnot(None)).all()
        for mother in mothers:
            days = (today - mother.delivery_date).days
            if days not in CHECKIN_DAYS:
                continue

            sent = {int(x) for x in (mother.checkins_sent or "").split(",") if x.strip().isdigit()}
            if days in sent:
                continue

            sent.add(days)
            mother.checkins_sent = ",".join(str(x) for x in sorted(sent))
            db.commit()
            try:
                await send_checkin(mother.wa_id, days)
            except Exception:
                logger.exception("Check-in delivery failed for %s on day %s", mother.wa_id, days)
                sent.discard(days)
                mother.checkins_sent = ",".join(str(x) for x in sorted(sent))
                db.commit()
    finally:
        db.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_checkins, "interval", hours=1, id="postpartum_checkins", replace_existing=True)
    scheduler.start()
    logger.info("Care Sister scheduler started")
    return scheduler
