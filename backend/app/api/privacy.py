"""Ẩn thông tin cá nhân của trang trại với người không có quyền xem."""
from app.api.deps import is_staff
from app.schemas.farm import FarmResponse
from app.schemas.user import UserResponse


def farm_view(farm, user: UserResponse) -> FarmResponse:
    """Trả FarmResponse.

    Admin và cán bộ thú y thấy đầy đủ. Chủ trại (tài khoản được gán cho trang trại) thấy thông tin
    liên hệ của chính trang trại mình. Người khác không thấy chủ trại, điện thoại, email, địa chỉ.
    Tài khoản sở hữu (owner_user_id) chỉ dành cho nhân viên.
    """
    view = FarmResponse.model_validate(farm)
    if is_staff(user):
        return view
    if farm.owner_user_id is not None and farm.owner_user_id == user.id:
        return view.model_copy(update={"owner_user_id": None})
    return view.model_copy(
        update={"owner_name": None, "phone": None, "email": None, "address": None, "owner_user_id": None}
    )


__all__ = ["farm_view"]
