"""鉴权模块"""

from fastapi import APIRouter, HTTPException, Depends
from src.auth.schemas import (
    IsOpenManagePayload,
    IsOpenManageResponse,
    RefreshTokenResponse,
)
from src.auth.service import (
    verify_signature,
    decrypt_device_id,
    MANAGED_DEVICES,
)
from src.utils.http import create_tokens, success_response, get_current_refresh_device
from src.utils.schemas import Response

router = APIRouter()


@router.post("/isOpenManage")
def is_open_manage(payload: IsOpenManagePayload) -> Response[IsOpenManageResponse]:
    """判断设备是否在管理设备列表中"""
    if not verify_signature(payload.id, payload.sig):
        raise HTTPException(status_code=403, detail="签名无效")

    try:
        device_id = decrypt_device_id(payload.id, payload.iv)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="解密失败") from exc

    token_bundle = create_tokens(device_id)
    is_manage = device_id in MANAGED_DEVICES

    res = IsOpenManageResponse(
        isOpenManage=is_manage,
        token=token_bundle["token"],
        refreshToken=token_bundle["refreshToken"],
    )
    return success_response(res)


@router.post("/refresh")
def refresh_token(
    device_id: str = Depends(get_current_refresh_device),
) -> Response[RefreshTokenResponse]:
    """刷新Token"""
    tokens = create_tokens(device_id)
    res = RefreshTokenResponse(
        token=tokens["token"], refreshToken=tokens["refreshToken"]
    )
    return success_response(res)
