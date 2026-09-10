"""通知器：站内信（写 alert 即站内）+ 邮件（SMTP 未配置降级仅站内）。"""
import smtplib
from abc import ABC, abstractmethod
from email.mime.text import MIMEText


class Notifier(ABC):
    name: str = ""

    @abstractmethod
    def send(self, alert, settings: dict) -> bool:
        """返回是否成功发送。"""


class InAppNotifier(Notifier):
    name = "站内信"

    def send(self, alert, settings: dict) -> bool:
        return True  # alert 本身即站内通知


class EmailNotifier(Notifier):
    name = "邮件"

    def send(self, alert, settings: dict) -> bool:
        cfg = settings.get("smtp", {})
        return self.send_raw(cfg, f"[StockWise] {alert.level}·{alert.title}", f"{alert.detail}\n建议：{alert.advice}")

    def send_raw(self, cfg: dict, subject: str, body: str) -> bool:
        """发送邮件；SMTP 未配置或发送失败返回 False（降级仅站内）。"""
        host = cfg.get("host")
        to = cfg.get("to") or []
        if not host or not to:
            return False
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = cfg.get("from") or cfg.get("user") or "stockwise@example.com"
            msg["To"] = ", ".join(to)
            with smtplib.SMTP_SSL(host, cfg.get("port", 465), timeout=10) as server:
                if cfg.get("user"):
                    server.login(cfg["user"], cfg.get("password", ""))
                server.sendmail(msg["From"], to, msg.as_string())
            return True
        except Exception:
            return False


def notify(alert, settings: dict) -> dict:
    """按预警级别选择通知渠道，返回 notify_log。

    紧急：实时邮件；一般/滞销：标记进入每日汇总（由调度进程统一发送）。
    """
    log = {"inapp": True}
    email = EmailNotifier()
    if alert.level == "紧急":
        log["email"] = "sent" if email.send(alert, settings) else "degraded_no_smtp"
    else:
        log["email"] = "pending_digest"
    return log
