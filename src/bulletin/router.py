import json
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, and_, desc, select
from starlette.responses import StreamingResponse

from src.bulletin.models import BulletinDB
from src.bulletin.schemas import (BaseBulletinInfo, BulletinInfo, DatePayload,
                                  ListInVersionReturn)
from src.database import get_session
from src.version.models import Version

router = APIRouter()
def event_stream():
    while True:
        yield f"data: The current time is {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        time.sleep(1)

@router.get("/sse")
async def sse_endpoint():
    return StreamingResponse(event_stream(), media_type="text/event-stream")
    

@router.get("/query", response_model=BulletinDB)
def query(id: int | None = 1, session: Session = Depends(get_session)):
    statement = select(BulletinDB).where(BulletinDB.id == id)
    result = session.exec(statement)
    first_result = result.first()
    response = {}
    if first_result is not None:
        response = first_result.model_dump()
    session.close()
    return response


@router.post("/byDate")
def bulletin_by_date(payload: DatePayload, session: Session = Depends(get_session)):
    statement = select(BulletinDB)
    if payload.start_date and payload.end_date:
        statement = statement.where(
            and_(
                BulletinDB.bulletin_date >= payload.start_date.__str__(),
                BulletinDB.bulletin_date <= payload.end_date.__str__(),
            )
        )
        results = session.exec(statement).all()
        response = [result.model_dump() for result in results]
        session.close()
        return response
    else:
        return []


@router.get("/listInVersion")
def list_in_version(
    session: Session = Depends(get_session),
) -> list[ListInVersionReturn]:
    statement = select(Version, BulletinDB).where(BulletinDB.version_id == Version.id)
    results = session.exec(statement).all()
    version_dict = {}
    for version, bulletin in results:
        if version.id not in version_dict:
            version_dict[version.id] = ListInVersionReturn(id=version.id, acronyms=version.acronyms, list=[])
        if bulletin:
            version_dict[version.id].list.append(
                BaseBulletinInfo(date=bulletin.bulletin_date, orderId=bulletin.rank_id, totalLen=bulletin.total_leng)
            )

    version_list = list(version_dict.values())
    session.close()
    return version_list

@router.get("/new")
def new_bulletin(session: Session = Depends(get_session)) -> BulletinInfo:
    statement_new_bulletin = (
        select(BulletinDB,Version)
        .where(BulletinDB.version_id == Version.id)
        .order_by(desc(BulletinDB.bulletin_date)).limit(1)
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
    order = order = next((index for index, bulletin in enumerate(bulletin_list_by_version_id) if bulletin.id == bulletin_info.id), -1)
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
    session.close()
    return bulletin_info
