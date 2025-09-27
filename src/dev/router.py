"""开发测试模块中的通用方法
"""
from pathlib import Path
from fastapi import APIRouter, Query

from src.bulletin.models import BulletinDB
from src.dev.service import test_resolve_notice
from src.nlp.train_model import train_model
from src.version.service import fix_bulletin_ranks
from src.bulletin.service import update_bulletin
from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.service import download_bulletin_list
from src.spiders.service import download_notice, resolve_notice

router = APIRouter()


@router.get("/testResolve")
async def test_resolve(
    test_date: str | None = Query(None, alias="testDate")
) -> dict[str, str | list[BulletinDB]]:
    """测试解析公告的路由
    Args:
        test_date (str | None): 测试的日期，默认为None, 表示测试所有公告
    """
    try:
        res_list: list[BulletinDB] = test_resolve_notice(test_date)
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


@router.get("/fixBulletinRanks")
def test_bulletin_ranks(version_id:int):
    """排序版本"""
    try:
        fix_bulletin_ranks(version_id)
        return {"message": "测试成功"}
    except Exception as e:
        return {"message": "测试失败", "error": str(e)}


@router.get("/fixAllBulletin")
def fix_all_bulletin(page_num: int = Query(1, alias="pageNum")):
    """补全全部公告"""
    try:
        bulletin_list: list[DownloadBulletin] = download_bulletin_list(page_num,False)
        for bulletin_info in bulletin_list:
            content_url: Path | None = download_notice(bulletin_info)
            bulletin: BulletinDB | None  = resolve_notice(content_path=content_url, bulletin_info = bulletin_info)
            if bulletin:
                update_bulletin(bulletin_info=bulletin)
        return {"message": "测试成功"}
    except Exception as e:
        return {"message": "测试失败", "error": str(e)}
