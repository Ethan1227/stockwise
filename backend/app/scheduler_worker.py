"""独立调度进程入口：python -m app.scheduler_worker。"""
from app.core.scheduler import run_scheduler_worker

if __name__ == "__main__":
    run_scheduler_worker()
