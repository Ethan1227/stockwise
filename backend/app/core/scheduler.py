"""进程内定时调度器（APScheduler）。每日测算任务由阶段 2 注册。"""
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def start_scheduler():
    """启动调度器（幂等）。"""
    if not scheduler.running:
        scheduler.start()
