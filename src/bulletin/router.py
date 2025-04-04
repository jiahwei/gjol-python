"""公告模块的接口

该模块定义了公告相关的接口，包括获取公告列表、下载公告列表、更新公告列表等功能。
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, and_, desc, select

from src.bulletin.models import BulletinDB
from src.bulletin.schemas import (
    BaseBulletinInfo,
    BulletinInfo,
    DatePayload,
    ListInVersionReturn,
)
from src.database import get_session
from src.version.models import Version

router = APIRouter()


@router.get("/query", response_model=BulletinDB)
def query(bulletin_id: int = 1, session: Session = Depends(get_session)):
    """
    根据公告ID查询公告信息

    Args:
        bulletin_id (int): 公告ID

    Returns:
        BulletinDB: 公告信息对象
    """
    statement = select(BulletinDB).where(BulletinDB.id == bulletin_id)
    result = session.exec(statement)
    first_result = result.first()

    if first_result is None:
        raise HTTPException(status_code=404, detail="未找到公告")

    return first_result


@router.post("/byDate", response_model=list[BulletinDB])
def bulletin_by_date(payload: DatePayload, session: Session = Depends(get_session)):
    """
    根据公告日期查询公告信息

    Args:
        payload (DatePayload): 公告日期载荷，包含开始日期和结束日期

    Returns:
        list[BulletinDB]: 符合日期条件的公告列表
    """
    if not (payload.start_date and payload.end_date):
        return []
    statement = select(BulletinDB).where(
        and_(
            BulletinDB.bulletin_date >= str(payload.start_date),
            BulletinDB.bulletin_date <= str(payload.end_date),
        )
    )
    results = session.exec(statement).all()
    return results


@router.get("/listInVersion", response_model=list[ListInVersionReturn])
def list_in_version(
    session: Session = Depends(get_session),
) -> list[ListInVersionReturn]:
    """
    获取按版本分组的公告列表

    Returns:
        list[ListInVersionReturn]: 按版本分组的公告列表
    """
    statement = select(Version, BulletinDB).where(BulletinDB.version_id == Version.id)
    results = session.exec(statement).all()
    version_dict = {}
    for version, bulletin in results:
        if version.id not in version_dict:
            version_dict[version.id] = ListInVersionReturn(
                id=version.id, acronyms=version.acronyms, list=[]
            )
        if bulletin:
            version_dict[version.id].list.append(
                BaseBulletinInfo(
                    date=bulletin.bulletin_date,
                    orderId=bulletin.rank_id,
                    totalLen=bulletin.total_leng,
                )
            )

    version_list = list(version_dict.values())
    return version_list


@router.get("/new", response_model=BulletinInfo)
def new_bulletin(session: Session = Depends(get_session)) -> BulletinInfo:
    """
    获取最新的公告信息

    Returns:
        BulletinInfo: 最新公告的详细信息
    """
    statement_new_bulletin = (
        select(BulletinDB, Version)
        .where(BulletinDB.version_id == Version.id)
        .order_by(desc(BulletinDB.bulletin_date))
        .limit(1)
    )
    result = session.exec(statement_new_bulletin).first()
    if result is None:
        raise HTTPException(status_code=404, detail="未找到公告")
    bulletin_info, version_info = result

    statement_bulletin = (
        select(BulletinDB)
        .where(BulletinDB.version_id == bulletin_info.version_id)
        .order_by(desc(BulletinDB.total_leng))
    )
    bulletin_list_by_version_id = session.exec(statement_bulletin).all()
    # 查找当前公告在列表中的位置
    order = next(
        (
            index
            for index, bulletin in enumerate(bulletin_list_by_version_id)
            if bulletin.id == bulletin_info.id
        ),
        -1,
    )
    content_arr = json.loads(bulletin_info.content_total_arr)
    # 构建返回的公告信息
    bulletin_info = BulletinInfo(
        id=bulletin_info.id,
        date=bulletin_info.bulletin_date,
        orderId=bulletin_info.rank_id,
        order=order,
        name=bulletin_info.bulletin_name,
        contentTotalArr=content_arr,
        versionId=version_info.id,
        versionName=version_info.name,
    )
    return bulletin_info
