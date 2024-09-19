import json, sqlite3, sys
from typing import Union, List, Optional
from fastapi import APIRouter,Depends
from constants import DEFAULT_SQLITE_PATH

from src.bulletin.schemas import DatePayload, Bulletin, getBulletinListInVersionReturn,bulletinAllInfo
from src.bulletin.models import Bulletin

from src.models import ArchiveDesc

from sqlmodel import Session, select
from src.database import get_session



router = APIRouter()


@router.get('/query')
def query(id: Optional[int] = 1, db: Session = Depends(get_session)):
    statement = select(Bulletin).where(Bulletin.id == id)
    result = db.exec(statement)
    return result.first()

@router.post('/byDate')
def bulletin_by_date(payload: DatePayload):
    conn = sqlite3.connect(DEFAULT_SQLITE_PATH)
    try:
        c = conn.cursor()
        if payload.show_all_info:
            sql_select = """
                SELECT * FROM bulletin WHERE bulletin_date BETWEEN ? AND ?
            """
        else:
            sql_select = """
                SELECT bulletin_date,total_leng FROM bulletin WHERE bulletin_date BETWEEN ? AND ?
            """
        c.execute(
            sql_select,
            (payload.start_date, payload.end_date),
        )
        rows = c.fetchall()
        conn.close()

        # 数据处理
        if payload.show_all_info:
            result = []
        else:
            result = [{"date": row[0], "totalLen": row[1]} for row in rows]
        return result
    except sqlite3.Error as e:
        return {"error": str(e)}
    
@router.get('/listInVersion')
def bulletin_list_in_version() -> List[getBulletinListInVersionReturn]:
    conn = sqlite3.connect(DEFAULT_SQLITE_PATH)
    try:
        cur = conn.cursor()
        sql_query_all_version = """
        SELECT id,acronyms from version
        """
        cur.execute(sql_query_all_version)
        version_rows = cur.fetchall()
        version_list = [
            getBulletinListInVersionReturn(id=row[0], acronyms=row[1], list=[])
            for row in version_rows
        ]
        sql_query_bulletin = """
        SELECT bulletin_date,total_leng,order_id FROM bulletin
        WHERE version_id = ?
        """
        for version in version_list:
            cur.execute(sql_query_bulletin, (version.id,))
            bulletin_row = cur.fetchall()
            formatted_data = [
                Bulletin(date=row[0], totalLen=row[1], orderId=row[2])
                for row in bulletin_row
            ]
            version.list = formatted_data
        return version_list
    except sqlite3.Error as e:
        return [getBulletinListInVersionReturn(id=-1, acronyms=str(e), list=[])]


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
        contentTotalArr = json_date,
        name=latest_row_date[4],
        versionID = latest_row_date[5]
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