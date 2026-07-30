## scheduler.py
# import
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from contextlib import asynccontextmanager
from fastapi import FastAPI
# from app.scheduler import setup_scheduler, scheduler

from src.core.memory import app_session

############################################################################
# timeouts
"""
scheduler.add_job(func, trigger=..., misfire_grace_time=3600
import time

@shared_task
def daily_report():
    start = time.perf_counter()
    logger.info("daily_report: started")

    try:
        result = generate_report()
        duration = time.perf_counter() - start
        logger.info(f"daily_report: completed in {duration:.1f}s, {result['count']} records")
    except Exception as e:
        duration = time.perf_counter() - start
        logger.error(f"daily_report: failed after {duration:.1f}s — {e}", exc_info=True)
        raise 
"""    
############################################################################
       
                  
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
# import logging

# 
if app_session.logger.session is None:
  hio = "" # create_logger(name="", logname="")
else:
  logger = app_session.logger

# Persistent job store — jobs survive restarts
# jobstores = {
#     'default': SQLAlchemyJobStore(url='postgresql://user:pass@localhost/mydb')
# }

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone='UTC')

def setup_scheduler():
    """Register all scheduled jobs."""

    scheduler.add_job(
        retrieve_mails,
        trigger=IntervalTrigger(minutes=30)
      # =CronTrigger(hour=8, minute=0),
        id='retrieve_mails',
        replace_existing=True,
        misfire_grace_time=3600,  # Run if missed within 1 hour
    )
    '''
    scheduler.add_job(
        warm_cache,
        trigger=IntervalTrigger(minutes=30),
        id='cache_warming',
        replace_existing=True,
    )

    scheduler.add_job(
        cleanup_expired_data,
        trigger=CronTrigger(hour=3, minute=0, day_of_week='sun'),
        id='weekly_cleanup',
        replace_existing=True,
    )
    '''

    scheduler.start()
    logger.info("Scheduler started with %d jobs", len(scheduler.get_jobs()))

'''
async def retrieve_mails():
    logger.info("Retrieving mails...")
    # Your retrieve logic here


async def warm_cache():
    logger.info("Warming product cache...")
    # Your cache warming logic here


async def cleanup_expired_data():
    logger.info("Running weekly cleanup...")
    # Your cleanup logic here
'''


############################# 
# create / delete reminder
#############################

@app.post("/api/reminders")
def create_reminder(data: ReminderCreate, user: User = Depends(get_current_user)):
    """User creates a custom reminder — scheduled dynamically."""
    job_id = f"reminder:{user.id}:{data.id}"

    scheduler.add_job(
        send_reminder_notification,
        trigger=CronTrigger(
            hour=data.hour,
            minute=data.minute,
            day_of_week=data.days,  # e.g., "mon,wed,fri"
        ),
        id=job_id,
        replace_existing=True,
        kwargs={"user_id": user.id, "message": data.message},
    )

    return {"job_id": job_id, "schedule": data.schedule_description}

@app.delete("/api/reminders/{reminder_id}")
def delete_reminder(reminder_id: str, user: User = Depends(get_current_user)):
    job_id = f"reminder:{user.id}:{reminder_id}"
    scheduler.remove_job(job_id)
    return {"deleted": True}
