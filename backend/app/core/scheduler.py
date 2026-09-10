"""进程内定时调度器（APScheduler）：每日 06:30 自动测算。"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import CALC_CRON_HOUR, CALC_CRON_MINUTE

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def _daily_calc_job():
    from app.core.db import SessionLocal
    from app.engine.pipeline import run_calc
    from app.services.alert import scan_alerts

    db = SessionLocal()
    try:
        run_calc(db)
        scan_alerts(db)
    finally:
        db.close()


def start_scheduler():
    """启动调度器并注册每日测算任务（幂等）。"""
    if not scheduler.running:
        scheduler.add_job(
            _daily_calc_job,
            CronTrigger(hour=CALC_CRON_HOUR, minute=CALC_CRON_MINUTE),
            id="daily_calc",
            replace_existing=True,
        )
        scheduler.start()
