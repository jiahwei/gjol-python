import json, sqlite3, sys
from typing import Union, List, Optional
from fastapi import APIRouter, Depends
from sqlmodel import Session, select, and_

from constants import DEFAULT_SQLITE_PATH
from src.bulletin.schemas import (
    DatePayload,
    BulletinInfo,
    getBulletinListInVersionReturn,
    bulletinAllInfo,
)
from src.bulletin.models import Bulletin, Version
from src.models import ArchiveDesc
from src.database import get_session


router = APIRouter()


@router.get("/query",response_model= Bulletin )
def query(id: Optional[int] = 1, session: Session = Depends(get_session)):
    statement = select(Bulletin).where(Bulletin.id == id)
    result = session.exec(statement)
    first_result = result.first()
    response = {}
    if first_result is not None:
        response = first_result.model_dump()
    session.close()
    return response


@router.post("/byDate")
def bulletin_by_date(payload: DatePayload, session: Session = Depends(get_session)):
    statement = (
        select(Bulletin)
        if payload.show_all_info
        else select(Bulletin.bulletin_date, Bulletin.total_leng)
    )
    if payload.start_date and payload.end_date:
        statement = statement.where(
            and_(
                Bulletin.bulletin_date >= payload.start_date.__str__(),
                Bulletin.bulletin_date <= payload.end_date.__str__(),
            )
        )
        results = session.exec(statement).all()
        response = []
        if payload.show_all_info:
            response = [
                result.model_dump()
                for result in results
                if isinstance(result, Bulletin)
            ]
        else:
            response = [{"bulletin_date": result[0], "total_leng": result[1]} for result in results] # type: ignore
        session.close()
        return response
    else:
        return []


# @router.get('/listInVersion')
# def bulletin_list_in_version() -> List[getBulletinListInVersionReturn]:
#     conn = sqlite3.connect(DEFAULT_SQLITE_PATH)
#     try:
#         cur = conn.cursor()
#         sql_query_all_version = """
#         SELECT id,acronyms from version
#         """
#         cur.execute(sql_query_all_version)
#         version_rows = cur.fetchall()
#         version_list = [
#             getBulletinListInVersionReturn(id=row[0], acronyms=row[1], list=[])
#             for row in version_rows
#         ]
#         sql_query_bulletin = """
#         SELECT bulletin_date,total_leng,order_id FROM bulletin
#         WHERE version_id = ?
#         """
#         for version in version_list:
#             cur.execute(sql_query_bulletin, (version.id,))
#             bulletin_row = cur.fetchall()
#             formatted_data = [
#                 Bulletin(date=row[0], totalLen=row[1], orderId=row[2])
#                 for row in bulletin_row
#             ]
#             version.list = formatted_data
#         return version_list
#     except sqlite3.Error as e:
#         return [getBulletinListInVersionReturn(id=-1, acronyms=str(e), list=[])]


def get_new_date(sqlitePath: str = DEFAULT_SQLITE_PATH) -> ArchiveDesc:
    """取最新日期的一条数据
    Args:
        sqlitePath(str):数据库路径
    Returns:
        str:数据库中最新一条公告的数据 ArchiveDesc
    """
    conn = sqlite3.connect(sqlitePath)
    cursor = conn.cursor()
    # 查询最新日期的一条数据
    cursor.execute("SELECT * FROM bulletin ORDER BY bulletin_date DESC LIMIT 1")
    latest_row_date: tuple = cursor.fetchone()
    conn.close()
    json_date = json.loads(latest_row_date[3])
    resolve_date = ArchiveDesc(
        date=latest_row_date[1],
        totalLen=latest_row_date[2],
        contentTotalArr=json_date,
        name=latest_row_date[4],
        versionID=latest_row_date[5],
    )
    return resolve_date


@router.get("/new")
def new_bulletin():
    info: ArchiveDesc = get_new_date()
    con = sqlite3.connect(DEFAULT_SQLITE_PATH)
    try:
        cur = con.cursor()
        sql_query_version = """
        SELECT acronyms from version where id = ?
        """
        cur.execute(sql_query_version, (info.versionID,))
        rows = cur.fetchone()
        archive_info = info.model_dump(exclude={"contentArr", "authors"})
        archive_info["reselseName"] = rows[0]

        sql_query_bulletin = """
        SELECT bulletin_date,total_leng FROM bulletin
        WHERE version_id = ?
        ORDER BY total_leng DESC
        """
        cur.execute(sql_query_bulletin, (info.versionID,))
        archive_list = cur.fetchall()
        order = 0
        for i, tup in enumerate(archive_list):
            if tup[0] == info.date:
                order = i
                break
        archive_info["order"] = order
        con.close()
        return archive_info
    except sqlite3.Error as e:
        return {"error": str(e)}
