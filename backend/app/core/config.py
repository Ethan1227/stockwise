"""应用配置：环境变量 + 业务参数默认值。

业务参数（权重/系数档位/阈值/备货周期/预算/大促日历）一律先在此声明默认值，
再由 seed 写入 settings 表；代码运行期只从 settings 读取，禁止硬编码数字。
"""
import os
from pathlib import Path

# 路径：backend/app/core/config.py -> backend/ -> 项目根
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"

# 数据库连接串：环境变量优先，默认 SQLite 单文件 data/stockwise.db
DEFAULT_DB_PATH = DATA_DIR / "stockwise.db"
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH.as_posix()}")

# 每日测算调度时间（可用环境变量覆盖，默认 06:30）
CALC_CRON_HOUR = int(os.getenv("CALC_CRON_HOUR", "6"))
CALC_CRON_MINUTE = int(os.getenv("CALC_CRON_MINUTE", "30"))
# 一般/滞销预警邮件汇总发送时间（默认 18:00）
EMAIL_DIGEST_HOUR = int(os.getenv("EMAIL_DIGEST_HOUR", "18"))

# ---- 业务参数默认值（seed 时写入 settings 表，页面可改）----
DEFAULT_SETTINGS = {
    # 基线日销权重：近30天 / 近90天 / 去年同期
    "base_weights": {"30d": 0.5, "90d": 0.3, "yoy": 0.2},
    # 备货周期默认值（天）
    "safety_days": 10,
    "lead_transit_sea": 35,
    "lead_transit_air": 10,
    "lead_shelf_days": 5,
    # 月采购预算（元）
    "monthly_budget": 140000,
    # 预警阈值（四项）
    "alert_thresholds": {
        "stockout_urgent_days": 10,   # 缺货紧急：可售天数 < 安全天数（需空运）
        "stockout_normal_days": 35,   # 缺货一般：可售天数 < 海运头程
        "slow_severe_turnover": 120,  # 滞销严重：周转 > 120 天
        "slow_severe_age": 180,       # 滞销严重：库龄 > 180 天
        "slow_mild_turnover": 60,     # 滞销轻度：周转 > 60 天
    },
    # 四修正器档位
    "modifier_tiers": {
        "trend": {"strong_up": 1.2, "up": 1.1, "flat": 1.0, "down": 0.9},
        "trend_pct": {"strong_up": 30, "up": 10, "down": -10},
        "competitor": {"stockout": 0.1, "price_cut": -0.1},
        "event": {"hot": 1.3, "near": 1.1, "hot_ratio": 1.3},
        "env": {"min": 0.9, "max": 1.1},
    },
    # 大促日历（与 promotion_calendar.csv 一致；seed 时以 CSV 为准覆盖）
    "promotion_calendar": [
        {"event": "黑五网一", "event_date": "2026-11-27", "warehouse_deadline": "2026-11-10"},
        {"event": "圣诞季", "event_date": "2026-12-25", "warehouse_deadline": "2026-12-05"},
    ],
    # 邮件通知（SMTP 未配置时自动降级为仅站内）
    "smtp": {
        "host": "",
        "port": 465,
        "user": "",
        "password": "",
        "from": "",
        "to": [],
    },
    "email_digest_hour": 18,  # 一般/滞销预警邮件汇总发送时间
}
