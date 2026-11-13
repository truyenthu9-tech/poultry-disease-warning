"""Dịch vụ gửi thông báo cho người dùng qua ConsoleNotifier."""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.models.farm import Farm
from app.models.user import User
from app.models.enums import AlertStatusEnum


class Notifier(ABC):
    """Interface định nghĩa hợp đồng gửi thông báo."""

    @abstractmethod
    def notify_user(
        self,
        user: User,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Gửi thông báo cho người dùng.

        Args:
            user: Người dùng nhận thông báo
            message: Nội dung thông báo
            data: Dữ liệu bổ sung (optional)

        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        pass


class ConsoleNotifier(Notifier):
    """Placeholder notifier xuất logs ra console thay vì email/SMS."""

    def notify_user(
        self,
        user: User,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Gửi thông báo qua console output.

        Args:
            user: Người dùng nhận thông báo
            message: Nội dung thông báo
            data: Dữ liệu bổ sung (optional)

        Returns:
            True (placeholder - luôn thành công)
        """
        print(f"[ConsoleNotifier] Gửi thông báo cho {user.email}: {message}")
        if data:
            print(f"[ConsoleNotifier] Dữ liệu: {data}")
        return True


class AlertNotificationService:
    """Dịch vụ tạo và gửi notifications khi có alert mới."""

    def __init__(self, notifier: Notifier = ConsoleNotifier()):
        self.notifier = notifier

    def notify_users_of_alert(
        self,
        db: Session,
        alert_id: str,
        risk_level: str,
    ) -> list[str]:
        """
        Gửi thông báo đến tất cả user liên quan đến farm trong area của alert.

        Args:
            db: Database session (AsyncSession hoặc Sync) - inject explicit
            alert_id: ID của alert cần gửi thông báo
            risk_level: Mức độ nguy hiểm để filter user

        Returns:
            Danh sách email đã nhận thành công, không chứa email thất bại.

        Notes:
            - Nếu không có farm trong area hoặc không có user thì trả về []
            - ConsoleNotifier placeholder chỉ in ra logs
        """
        from app.models.alert import Alert

        # Lấy alert
        alert = db.query(Alert).filter(Alert.id == alert_id).first()

        if not alert:
            return []

        users_notified = []

        # Gửi notification cho mỗi user liên quan (placeholder logic)
        for user in db.query(User).all():  # Thực tế sẽ filter theo tỉnh/quận
            success = self.notifier.notify_user(
                user=user,
                message=f"[ALERT] Alert {alert_id}: {risk_level} - {alert.virus_type}",
                data={"alert_id": alert_id, "risk_level": risk_level},
            )

            if success:
                users_notified.append(user.email)

        return users_notified

    def notify_user_of_outbreak(
        self,
        user: User,
        outbreak_id: str,
        message: str,
        data: dict[str, Any] | None = None,
    ) -> bool:
        """
        Gửi thông báo cho user cụ thể về outbreak.

        Args:
            user: Người dùng nhận thông báo
            outbreak_id: ID ổ dịch liên quan
            message: Nội dung thông báo
            data: Dữ liệu bổ sung (optional)

        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        success = self.notifier.notify_user(user, message, data)
        return success


__all__ = ["Notifier", "ConsoleNotifier", "AlertNotificationService"]
