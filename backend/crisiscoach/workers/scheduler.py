"""Cron job scheduler — visa countdown, finance checks, interview prep (APScheduler)."""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


async def _run_visa_checks() -> None:
    from crisiscoach.db.supabase import get_client
    from crisiscoach.agents.background.visa_support_agent import run_for_user

    sb = get_client()
    users = sb.table("users").select("id").not_.is_("visa_deadline", "null").execute()
    for u in users.data:
        try:
            await run_for_user(u["id"])
        except Exception as e:
            logger.error(f"visa_check failed for {u['id']}: {e}")


async def _run_finance_checks() -> None:
    from crisiscoach.db.supabase import get_client
    from crisiscoach.agents.background.finance_check_agent import run_for_user

    sb = get_client()
    users = sb.table("users").select("id").eq("active", True).execute()
    for u in users.data:
        try:
            await run_for_user(u["id"])
        except Exception as e:
            logger.error(f"finance_check failed for {u['id']}: {e}")


async def _run_interview_prep() -> None:
    from crisiscoach.db.supabase import get_client
    from crisiscoach.agents.background.interview_prep import generate_prep_plan

    sb = get_client()
    users = sb.table("users").select("id").eq("active", True).execute()
    for u in users.data:
        try:
            await generate_prep_plan(u["id"])
        except Exception as e:
            logger.error(f"interview_prep failed for {u['id']}: {e}")


def build_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # Visa check — daily at 8 AM
    scheduler.add_job(_run_visa_checks, CronTrigger(hour=8, minute=0), id="visa_check")

    # Finance check — every Sunday at 9 AM
    scheduler.add_job(_run_finance_checks, CronTrigger(day_of_week="sun", hour=9), id="finance_check")

    # Interview prep — every Monday at 7 AM
    scheduler.add_job(_run_interview_prep, CronTrigger(day_of_week="mon", hour=7), id="interview_prep")

    return scheduler


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    scheduler = build_scheduler()
    scheduler.start()
    logger.info("scheduler: started")
    try:
        loop.run_forever()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
