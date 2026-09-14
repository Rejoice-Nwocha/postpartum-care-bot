import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal, Mother, CheckinDelivery
from app.whatsapp_client import send_text

logger = logging.getLogger(__name__)
CHECKIN_DAYS = (3, 7, 14)


async def send_checkin(wa_id: str, day: int):
    message = (
        f"Day {day} check-in, Mama.\n\n"
        "How are you feeling today? You can tell me about your recovery, emotions, "
        "body, breastfeeding, baby, food, sleep or anything else on your mind."
    )
    return await send_text(wa_id, message)


def claim_checkin(db, wa_id: str, day: int) -> bool:
    """Atomically claim a check-in so separate workers cannot both send it."""
    try:
        db.add(CheckinDelivery(wa_id=wa_id, day=day))
        db.commit()
        return True
    except IntegrityError:
        db.rollback()
        return False


async def run_checkins():
    """Send each due check-in once, including a late delivery after downtime."""
    db = SessionLocal()
    try:
        today = date.today()
        mothers = db.query(Mother).filter(Mother.delivery_date.isnot(None)).all()
        for mother in mothers:
            days_since_birth = (today - mother.delivery_date).days
            if days_since_birth < 0:
                continue

            sent = {int(x) for x in (mother.checkins_sent or "").split(",") if x.strip().isdigit()}
            due_days = [day for day in CHECKIN_DAYS if days_since_birth >= day and day not in sent]
            for day in due_days:
                if not claim_checkin(db, mother.wa_id, day):
                    sent.add(day)
                    mother.checkins_sent = ",".join(str(x) for x in sorted(sent))
                    db.commit()
                    continue

                try:
                    await send_checkin(mother.wa_id, day)
                except Exception:
                    logger.exception("Check-in delivery failed for %s on day %s", mother.wa_id, day)
                    db.query(CheckinDelivery).filter(
                        CheckinDelivery.wa_id == mother.wa_id,
                        CheckinDelivery.day == day,
                    ).delete(synchronize_session=False)
                    db.commit()
                    break

                sent.add(day)
                mother.checkins_sent = ",".join(str(x) for x in sorted(sent))
                db.commit()
                logger.info("Postpartum check-in delivered: wa_id=%s day=%s", mother.wa_id, day)
    finally:
        db.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_checkins,
        "interval",
        hours=1,
        id="postpartum_checkins",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info("Care Sister scheduler started")
    return scheduler
