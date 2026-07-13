from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import date

async def send_checkin(wa_id: str, day: int):
    # Placeholder - expand with full templates
    message = f"Day {day} check-in: How are you feeling today, Mama?"
    await send_text(wa_id, message)

def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Add jobs here later
    scheduler.start()
