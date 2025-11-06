"""公告模块的接口

该模块定义了公告相关的接口，包括获取公告列表、下载公告列表、更新公告列表等功能。
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, and_, desc, select
from collections.abc import Sequence

from src.bulletin.models import BulletinDB
from src.bulletin.schemas import (
    BulletinInfo,
    DatePayload,
    ListInVersionReturn,
    BulletinInVersion
)
from src.database import get_session
from src.version.models import Version
from src.utils.http import success_response
from src.utils.schemas import Response

router = APIRouter()


@router.get("/query", response_model=Response[BulletinDB])
def query(bulletin_id: int = 1, session: Session = Depends(get_session)) -> Response[BulletinDB]:
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

    return success_response(first_result)


@router.post("/byDate", response_model=list[BulletinDB])
def bulletin_by_date(payload: DatePayload, session: Session = Depends(get_session)) -> Response[Sequence[BulletinDB]]:
    """
    根据公告日期查询公告信息

    Args:
        payload (DatePayload): 公告日期载荷，包含开始日期和结束日期

    Returns:
        list[BulletinDB]: 符合日期条件的公告列表
    """
    if not (payload.start_date and payload.end_date):
        raise HTTPException(status_code=500, detail="payload 不能为空")
    statement = select(BulletinDB).where(
        and_(
            BulletinDB.bulletin_date >= str(payload.start_date),
            BulletinDB.bulletin_date <= str(payload.end_date),
        )
    )
    results = session.exec(statement).all()
    return success_response(results)


@router.get("/listInVersion", response_model=Response[list[ListInVersionReturn]])
def list_in_version(
    session: Session = Depends(get_session),
) -> Response[list[ListInVersionReturn]]:
    """
    获取按版本分组的公告列表

    Returns:
        list[ListInVersionReturn]: 按版本分组的公告列表
    """
    statement = select(Version, BulletinDB).where(BulletinDB.version_id == Version.id)
    results = session.exec(statement).all()
    version_dict: dict[int | None, ListInVersionReturn] = {}

    # 首先按版本ID分组所有公告
    bulletins_by_version: dict[int | None, list[BulletinDB]] = {}
    for version, bulletin in results:
        if version.id not in version_dict:
            start_date = version.start_date if version.start_date else ''
            end_date = version.end_date if version.end_date else ''
            version_dict[version.id] = ListInVersionReturn(
                id=version.id, acronyms=version.acronyms, list=[], start=start_date, end=end_date
            )
            bulletins_by_version[version.id] = []
        if bulletin:
            bulletins_by_version[version.id].append(bulletin)

    # 对每个版本的公告按时间排序
    for version_id, bulletins in bulletins_by_version.items():
        sorted_bulletins = sorted(bulletins, key=lambda b: b.bulletin_date, reverse=False)

        version_dict[version_id].total_version_len = sum(
            item.total_leng for item in bulletins
        )
        # 添加到结果中，并计算排名
        for rank, bulletin in enumerate(sorted_bulletins, 1):
            version_dict[version_id].list.append(
                BulletinInVersion(
                    date=bulletin.bulletin_date,
                    orderId=rank,
                    totalLen=bulletin.total_leng,
                    type=bulletin.content_total_arr,
                )
            )

    version_list = list(version_dict.values())
    return success_response(version_list)


@router.get("/new", response_model=Response[BulletinInfo])
def new_bulletin(session: Session = Depends(get_session)) -> Response[BulletinInfo]:
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

    # 获取同版本下的所有公告，用于计算排名
    statement_all_bulletins = select(BulletinDB).where(
        BulletinDB.version_id == bulletin_info.version_id
    )
    all_bulletins = session.exec(statement_all_bulletins).all()

    # 按字数排序（降序）并计算排名
    bulletins_by_length = sorted(
        all_bulletins, key=lambda x: x.total_leng, reverse=True
    )
    order = next(
        (
            index
            for index, bulletin in enumerate(bulletins_by_length)
            if bulletin.id == bulletin_info.id
        ),
        -1,
    )

    content_arr = json.loads(bulletin_info.content_total_arr)

    # 构建返回的公告信息
    bulletin_info_obj = BulletinInfo(
        id=bulletin_info.id,
        date=bulletin_info.bulletin_date,
        order=order,
        order_by_date=len(all_bulletins),
        name=bulletin_info.bulletin_name,
        contentTotalArr=content_arr,
        versionId=version_info.id,
        versionName=version_info.name,
    )
    return success_response(bulletin_info_obj)
