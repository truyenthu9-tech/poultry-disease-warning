"""Gửi thông báo cảnh báo: console, email (SMTP) và bộ gộp nhiều kênh."""
import asyncio
import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from email.message import EmailMessage
from email.utils import formataddr
from html import escape

from app.core.config import settings
from app.models.alert import Alert
from app.models.farm import Farm
from app.services.risk_service import ADVISORY_NOTICE

logger = logging.getLogger(__name__)

RISK_LABEL = {"low": "Thấp", "medium": "Trung bình", "high": "Cao", "critical": "Nghiêm trọng"}


class Notifier(ABC):
    @abstractmethod
    async def send(self, alert: Alert, farm: Farm) -> None:
        """Gửi thông báo, ném exception nếu thất bại."""


class ConsoleNotifier(Notifier):
    async def send(self, alert: Alert, farm: Farm) -> None:
        logger.info(
            "[ALERT %s] trang trại %s (%s): %s",
            alert.risk_level.value, farm.name, farm.owner_name, alert.message,
        )
        print(f"[ConsoleNotifier] {alert.risk_level.value.upper()} -> {farm.name}: {alert.message}")


def build_alert_email(alert: Alert, farm: Farm) -> EmailMessage:
    """Dựng nội dung email gồm bản chữ thường và bản HTML."""
    risk = RISK_LABEL.get(alert.risk_level.value, alert.risk_level.value)
    sender = settings.SMTP_FROM or settings.SMTP_USER

    msg = EmailMessage()
    msg["Subject"] = f"[Cảnh báo dịch gia cầm] Mức {risk} - {farm.name}"
    msg["From"] = formataddr((settings.SMTP_FROM_NAME, sender))
    msg["To"] = farm.email

    basis = alert.risk_basis or ""
    text = (
        f"Kính gửi {farm.owner_name},\n\n"
        f"{alert.message}\n\n"
        f"Mức nguy cơ: {risk}\n"
        f"Khoảng cách tới ổ dịch: {alert.distance_km:.2f} km\n"
        + (f"Cơ sở đánh giá: {basis}\n" if basis else "")
        + "\n"
        "Vui lòng tăng cường vệ sinh, hạn chế người và phương tiện ra vào trại, "
        "và liên hệ cán bộ thú y nếu thấy gia cầm có dấu hiệu bất thường.\n\n"
        f"{ADVISORY_NOTICE}\n"
    )
    html = (
        f"<p>Kính gửi <b>{escape(farm.owner_name)}</b>,</p>"
        f"<p>{escape(alert.message)}</p>"
        f"<ul><li>Mức nguy cơ: <b>{escape(risk)}</b></li>"
        f"<li>Khoảng cách tới ổ dịch: <b>{alert.distance_km:.2f} km</b></li>"
        + (f"<li>Cơ sở đánh giá: {escape(basis)}</li>" if basis else "")
        + "</ul>"
        "<p>Vui lòng tăng cường vệ sinh, hạn chế người và phương tiện ra vào trại, "
        "và liên hệ cán bộ thú y nếu thấy gia cầm có dấu hiệu bất thường.</p>"
        f"<p><i>{escape(ADVISORY_NOTICE)}</i></p>"
    )
    msg.set_content(text)
    msg.add_alternative(html, subtype="html")
    return msg


def _send_smtp(msg: EmailMessage) -> None:
    """Gửi email bằng smtplib. Hàm này chặn luồng nên được gọi qua asyncio.to_thread."""
    timeout = settings.SMTP_TIMEOUT
    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout,
            context=ssl.create_default_context(),
        )
    else:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=timeout)
    with server:
        if settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL:
            server.starttls(context=ssl.create_default_context())
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)


class EmailNotifier(Notifier):
    """Gửi email tới địa chỉ email của trang trại.

    Trang trại không có email thì bỏ qua, không coi là lỗi.
    Lỗi SMTP được ném ra để cảnh báo được đánh dấu FAILED.
    """

    async def send(self, alert: Alert, farm: Farm) -> None:
        if not farm.email:
            logger.info("Trang trại %s chưa có email, bỏ qua gửi email.", farm.name)
            return
        msg = build_alert_email(alert, farm)
        await asyncio.to_thread(_send_smtp, msg)
        logger.info("Đã gửi email cảnh báo tới %s (%s).", farm.email, farm.name)


class CompositeNotifier(Notifier):
    """Gửi qua nhiều kênh. Một kênh lỗi không chặn các kênh còn lại."""

    def __init__(self, notifiers: list[Notifier]) -> None:
        self.notifiers = notifiers

    async def send(self, alert: Alert, farm: Farm) -> None:
        errors: list[str] = []
        for notifier in self.notifiers:
            try:
                await notifier.send(alert, farm)
            except Exception as exc:
                logger.exception("Kênh %s gửi lỗi", type(notifier).__name__)
                errors.append(f"{type(notifier).__name__}: {exc}")
        if errors:
            raise RuntimeError("; ".join(errors))


def get_default_notifier() -> Notifier:
    """Console luôn bật. Thêm email khi cấu hình SMTP đầy đủ."""
    notifiers: list[Notifier] = [ConsoleNotifier()]
    if settings.email_ready:
        notifiers.append(EmailNotifier())
    return CompositeNotifier(notifiers) if len(notifiers) > 1 else notifiers[0]


__all__ = [
    "Notifier", "ConsoleNotifier", "EmailNotifier", "CompositeNotifier",
    "build_alert_email", "get_default_notifier",
]
