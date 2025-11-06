""" 鉴权模块
"""
from fastapi import APIRouter, HTTPException
from src.auth.schemas import IsOpenManagePayload,IsOpenManageResponse
from src.auth.service import verify_signature,decrypt_android_id,MANAGED_DEVICES

router = APIRouter()

@router.post("/isOpenManage")
def is_open_manage(payload: IsOpenManagePayload) -> IsOpenManageResponse:
    """ 判断设备是否在管理设备列表中

    Args:
        payload (IsOpenManagePayload): 认证服务的入参类型

    Returns:
        IsOpenManageResponse: 认证服务的出参类型
    """
    if not verify_signature(payload.id, payload.sig):
        raise HTTPException(status_code=403, detail="签名无效")

    try:
        android_id = decrypt_android_id(payload.id,payload.iv)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="解密失败")

    return {"isOpenManage": android_id in MANAGED_DEVICES}
