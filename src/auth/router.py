""" 鉴权模块
"""
from fastapi import APIRouter, HTTPException
from src.auth.schemas import IsOpenManagePayload,IsOpenManageResponse
from src.auth.service import verify_signature,decrypt_device_id,MANAGED_DEVICES
from src.utils.http import success_response
from src.utils.schemas import Response

router = APIRouter()

@router.post("/isOpenManage")
def is_open_manage(payload: IsOpenManagePayload) -> Response[IsOpenManageResponse]:
    """ 判断设备是否在管理设备列表中

    Args:
        payload (IsOpenManagePayload): 认证服务的入参类型

    Returns:
        Response[IsOpenManageResponse]: 认证服务的出参类型
    """
    if not verify_signature(payload.id, payload.sig):
        raise HTTPException(status_code=403, detail="签名无效")

    try:
        device_id = decrypt_device_id(payload.id,payload.iv)
    except Exception:
        raise HTTPException(status_code=400, detail="解密失败")

    return success_response(IsOpenManageResponse(isOpenManage=device_id in MANAGED_DEVICES))
