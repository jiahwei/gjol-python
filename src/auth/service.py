"""鉴权模块的业务逻辑
"""
import os
import base64
import binascii
import hmac
import hashlib

from fastapi import HTTPException
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dotenv import load_dotenv

# 加载密钥
_ = load_dotenv()
_AES_KEY = os.getenv("AES_KEY")
_HMAC_SECRET = os.getenv("HMAC_SECRET")
raw_devices = os.getenv("MANAGED_DEVICES", "")
# 加载管理设备列表，保存设备ID的哈希值
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


def decrypt_device_id(encrypted_id: str,iv:str) -> str:
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
