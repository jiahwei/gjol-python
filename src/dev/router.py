from fastapi import APIRouter,Query
from src.dev.service import test_resolve_notice


router = APIRouter()

@router.get("/test-resolve")
async def test_resolve(test_date: str | None = Query(None,alias="testDate")):
    """测试解析公告的路由
    Args:
        test_date (str | None): 测试的日期，默认为None, 表示测试所有公告
    """
    try:
        result = test_resolve_notice(test_date)
        return {"message": "测试成功", "result": result}
    except Exception as e:
        return {"message": "测试失败", "error": str(e)}