"""鉴权模块的业务逻辑
"""
import os
import base64
import binascii
import hmac
import hashlib

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore
from dotenv import load_dotenv
import jwt, time
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError


from src.auth.schemas import CreateTokenPayload
# 加载密钥
_ = load_dotenv()
_AES_KEY = os.getenv("AES_KEY")
_HMAC_SECRET = os.getenv("HMAC_SECRET")
_JWT_SECRET = os.getenv("JWT_SECRET")
raw_devices = os.getenv("MANAGED_DEVICES", "")
# 加载管理设备列表，保存设备ID的哈希值
MANAGED_DEVICES = set(device.strip() for device in raw_devices.split(",") if device.strip())

if not _AES_KEY or not _HMAC_SECRET or not _JWT_SECRET:
    raise ValueError("AES_KEY and HMAC_SECRET and JWT_SECRET must be set in the environment variables")

AES_KEY = binascii.unhexlify(_AES_KEY)
HMAC_SECRET: str = _HMAC_SECRET
JWT_SECRET: str = _JWT_SECRET



aesgcm: AESGCM = AESGCM(AES_KEY)

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
        ciphertext: bytes = base64.b64decode(encrypted_id)
        nonce: bytes = base64.b64decode(iv)
        plaintext: bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")

    except Exception as e:
        print(f"Decryption failed: {e}")
        raise HTTPException(status_code=400, detail=f"解密失败: {str(e)}")


def creat_token(device_id: str) -> str:
    """创建token
    """
    payload_model = CreateTokenPayload(
        sub=device_id,
        exp=int(time.time()) + 3600,
        scope="manage"
    )
    payload: dict[str, int | str] = payload_model.model_dump()
    return str(jwt.encode(payload, JWT_SECRET, algorithm="HS256"))


def verify_token(token: str) -> CreateTokenPayload:
    payload: dict[str, int | str] = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    return CreateTokenPayload.model_validate(payload)


security = HTTPBearer()
DependsSecurity = Depends(security)


def get_current_device(credentials: HTTPAuthorizationCredentials = DependsSecurity) -> str:
    token = credentials.credentials
    try:
        data = verify_token(token)
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token已过期")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token无效")

    if data.scope != "manage":
        raise HTTPException(status_code=403, detail="权限不足")

    if not data.sub:
        raise HTTPException(status_code=400, detail="Token缺少设备标识")
    return data.sub
