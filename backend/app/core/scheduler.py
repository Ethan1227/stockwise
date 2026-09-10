"""独立调度进程（APScheduler）：每日 06:30 测算 + 预警扫描，与 API 进程解耦。"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import CALC_CRON_HOUR, CALC_CRON_MINUTE


def daily_calc_job():
    """每日测算 + 预警扫描（定时任务入口）。"""
    from app.core.db import SessionLocal
    from app.engine.pipeline import run_calc
    from app.services.alert import scan_alerts

    db = SessionLocal()
    try:
        run_calc(db)
        scan_alerts(db)
    finally:
        db.close()


def run_scheduler_worker():
    """独立调度进程入口：阻塞运行，直至收到终止信号。"""
    scheduler = BlockingScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(
        daily_calc_job,
        CronTrigger(hour=CALC_CRON_HOUR, minute=CALC_CRON_MINUTE),
        id="daily_calc",
        replace_existing=True,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown(wait=False)
