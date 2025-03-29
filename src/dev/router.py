from fastapi import APIRouter
from src.dev.service import test_resolve_notice


router = APIRouter()

@router.get("/test-resolve")
async def test_resolve():
    """测试解析公告的路由"""
    try:
        result = test_resolve_notice()
        return {"message": "测试成功", "result": result}
    except Exception as e:
        return {"message": "测试失败", "error": str(e)}