"""Đánh giá mức nguy cơ của một trang trại đối với một ổ dịch.

Đây là công cụ cảnh báo tham khảo, không thay thế đánh giá dịch tễ của cơ quan thú y.
Mức nguy cơ chỉ dựa trên hai yếu tố mà hệ thống thực sự có dữ liệu:

1. Khoảng cách từ trang trại tới ổ dịch, so với các ngưỡng RISK_*_KM trong cấu hình.
2. Mức độ nghiêm trọng của ổ dịch do cán bộ nhập. Ổ dịch nghiêm trọng thì trang trại trong
   bán kính cảnh báo không bị xếp thấp hơn một mức tối thiểu. Yếu tố này chỉ nâng mức, không
   bao giờ hạ mức, để không bỏ sót trang trại ở gần.

Hệ thống không xét hướng gió, đường vận chuyển, loài gia cầm, tình trạng tiêm phòng hay
các yếu tố dịch tễ khác. Các ngưỡng mặc định cần cơ quan thú y có thẩm quyền rà soát
trước khi dùng cho trang trại thật.
"""
from dataclasses import dataclass

from app.core.config import settings
from app.models.enums import RiskLevel, Severity

ADVISORY_NOTICE = (
    "Đây là cảnh báo tham khảo do hệ thống tính từ vị trí địa lý và thông tin ổ dịch đã nhập, "
    "không phải kết luận chẩn đoán hay chỉ đạo chính thức của cơ quan thú y. "
    "Hãy liên hệ cán bộ thú y địa phương để được hướng dẫn."
)

_ORDER = (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)
_LABEL = {
    RiskLevel.LOW: "Thấp",
    RiskLevel.MEDIUM: "Trung bình",
    RiskLevel.HIGH: "Cao",
    RiskLevel.CRITICAL: "Nghiêm trọng",
}
_SEVERITY_LABEL = {
    Severity.LOW: "Thấp",
    Severity.MEDIUM: "Trung bình",
    Severity.HIGH: "Cao",
    Severity.CRITICAL: "Nghiêm trọng",
}
# Mức nguy cơ tối thiểu cho trang trại trong bán kính cảnh báo, theo mức độ của ổ dịch
_SEVERITY_FLOOR = {
    Severity.LOW: RiskLevel.LOW,
    Severity.MEDIUM: RiskLevel.MEDIUM,
    Severity.HIGH: RiskLevel.HIGH,
    Severity.CRITICAL: RiskLevel.CRITICAL,
}


@dataclass(frozen=True)
class RiskAssessment:
    level: RiskLevel
    basis: str


def distance_risk(distance_km: float) -> RiskLevel:
    """Mức nguy cơ chỉ theo khoảng cách."""
    if distance_km <= settings.RISK_CRITICAL_KM:
        return RiskLevel.CRITICAL
    if distance_km <= settings.RISK_HIGH_KM:
        return RiskLevel.HIGH
    if distance_km <= settings.RISK_MEDIUM_KM:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def assess_risk(distance_km: float, severity: Severity) -> RiskAssessment:
    """Mức nguy cơ cuối cùng và cơ sở đánh giá, để lưu cùng cảnh báo."""
    by_distance = distance_risk(distance_km)
    floor = _SEVERITY_FLOOR[severity]
    level = max(by_distance, floor, key=_ORDER.index)
    basis = (
        f"Theo khoảng cách ({distance_km:.2f} km): {_LABEL[by_distance]}. "
        f"Theo mức độ ổ dịch ({_SEVERITY_LABEL[severity]}): tối thiểu {_LABEL[floor]}. "
        f"Kết luận: {_LABEL[level]}. "
        "Chưa xét hướng gió, đường vận chuyển, loài gia cầm và các yếu tố dịch tễ khác."
    )
    return RiskAssessment(level=level, basis=basis)


__all__ = ["ADVISORY_NOTICE", "RiskAssessment", "distance_risk", "assess_risk"]
