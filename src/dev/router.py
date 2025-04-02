from fastapi import APIRouter,Query


from src.bulletin.models import BulletinDB
from src.dev.service import test_resolve_notice
from src.nlp.train_model import train_model


router = APIRouter()

@router.get("/testResolve")
async def test_resolve(test_date: str | None = Query(None,alias="testDate")) -> dict[str,  str | list[BulletinDB] ]:
    """测试解析公告的路由
    Args:
        test_date (str | None): 测试的日期，默认为None, 表示测试所有公告
    """
    try:
        res_list:list[BulletinDB] =  test_resolve_notice(test_date)
        return {"message": "测试成功", "data": res_list}
    except Exception as e:
        return {"message": "测试失败", "error": str(e)}


@router.get("/tranModel")
def tran_model():
    """训练模型"""
    try:
        train_model()
        return {"message": "测试成功"}
    except Exception as e:
        return {"message": "测试失败", "error": str(e)}
    