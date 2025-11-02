"""
认证服务
"""
import os
import base64
from fastapi import APIRouter, HTTPException

import hmac, hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
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

# Assert that AES_KEY and HMAC_SECRET are strings after the check
AES_KEY: str = _AES_KEY
HMAC_SECRET: str = _HMAC_SECRET

FIXED_IV = b'\x00' * 16

def verify_signature(encrypted_id: str, signature: str) -> bool:
    expected = hmac.new(HMAC_SECRET.encode(), encrypted_id.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def decrypt_android_id(encrypted_id: str) -> str:
    try:
        # 解码 base64 密文
        encrypted_bytes = base64.b64decode(encrypted_id)

        # 检查密钥长度
        key_bytes = AES_KEY.encode()
        if len(key_bytes) != 32:
            raise ValueError(f"AES 密钥长度错误，应为 32 字节，当前为 {len(key_bytes)} 字节")

        # 创建 AES-CBC 解密器
        cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(FIXED_IV), backend=default_backend())
        decryptor = cipher.decryptor()

        # 解密并去除填充
        decrypted_padded = decryptor.update(encrypted_bytes) + decryptor.finalize()
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        decrypted_bytes = unpadder.update(decrypted_padded) + unpadder.finalize()

        # 打印调试信息
        print("Encrypted base64:", encrypted_id)
        print("Key length:", len(key_bytes))
        print("IV length:", len(FIXED_IV))
        print("Encrypted bytes (first 16):", encrypted_bytes[:16])
        print("Decrypted bytes:", decrypted_bytes[:32])

        # return decrypted_bytes.decode('utf-8')
        return decrypted_bytes.hex()

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
        android_id = decrypt_android_id(payload.id)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=400, detail="解密失败")

    return {"isOpenManage": android_id in MANAGED_DEVICES}
