"""
认证服务
"""
import os
import base64
import binascii
from fastapi import APIRouter, HTTPException

import hmac, hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv
from src.auth.schemas import AuthPayload

router = APIRouter()

# 加载密钥
_ = load_dotenv()
_AES_KEY = os.getenv("AES_KEY")
_HMAC_SECRET = os.getenv("HMAC_SECRET")
raw_devices = os.getenv("MANAGED_DEVICES", "")
MANAGED_DEVICES = set(device.strip() for device in raw_devices.split(",") if device.strip())

if not _AES_KEY or not _HMAC_SECRET:
    raise ValueError("AES_KEY and HMAC_SECRET must be set in the environment variables")

AES_KEY = binascii.unhexlify(_AES_KEY)
HMAC_SECRET: str = _HMAC_SECRET

aesgcm = AESGCM(AES_KEY)

def verify_signature(encrypted_id: str, signature: str) -> bool:
    """验签

    Args:
        encrypted_id (str): _description_
        signature (str): _description_

    Returns:
        bool: _description_
    """    
    expected = hmac.new(HMAC_SECRET.encode(), encrypted_id.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def decrypt_android_id(encrypted_id: str,iv:str) -> str:
    """解密

    Args:
        encrypted_id (str): _description_

    Raises:
        ValueError: _description_
        HTTPException: _description_

    Returns:
        str: _description_
    """
    try:
        ciphertext = base64.b64decode(encrypted_id)
        nonce = base64.b64decode(iv)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode("utf-8")

    except Exception as e:
        print(f"Decryption failed: {e}")
        raise HTTPException(status_code=400, detail=f"解密失败: {str(e)}")


@router.post("/isOpenManage")
def is_open_manage(payload: AuthPayload):
    """判断是否开启管理功能

    Args:
        payload (AuthPayload): 认证服务的入参类型

    Returns:
        bool: 是否开启了管理功能
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
