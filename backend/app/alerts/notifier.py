"""通知器：站内信（写 alert 即站内）+ 邮件（SMTP 未配置降级仅站内）。"""
from abc import ABC, abstractmethod


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
        smtp = settings.get("smtp")
        if not smtp:
            return False  # SMTP 未配置 -> 降级仅站内
        # TODO(dev): 接入真实 SMTP 发送
        return True


def notify(alert, settings: dict) -> dict:
    """按预警级别选择通知渠道，返回 notify_log。"""
    log = {"inapp": True}
    email = EmailNotifier()
    # 紧急级实时尝试邮件；未配置 SMTP 自动降级仅站内
    if alert.level == "紧急":
        log["email"] = "sent" if email.send(alert, settings) else "degraded_no_smtp"
    return log
