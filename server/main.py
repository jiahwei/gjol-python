from typing import Union, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from datetime import date
import json, sqlite3, sys
from constants import DEFAULT_SQLITE_PATH

from util.sqlite import get_new_date
from util.type import ArchiveDesc

app = FastAPI()


class DatePayload(BaseModel):
    start_date: Optional[date] = Field(alias="startDate")
    end_date: Optional[date] = Field(alias="endDate")
    show_all_info: bool = Field(default=False, alias="showAllInfo")


@app.post("/getBulletinByDate")
def get_bulletin_by_date(payload: DatePayload):
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

class Bulletin(BaseModel):
    date: str = ""
    orderId:int = 0
    totalLen:int = 0
class getBulletinListInVersionReturn(BaseModel):
    id: int 
    acronyms: str
    list: List[Bulletin]

@app.get("/getBulletinListInVersion")
def get_bulletin_list_in_version() -> List[getBulletinListInVersionReturn]:
    conn = sqlite3.connect(DEFAULT_SQLITE_PATH)
    try:
        cur = conn.cursor()
        sql_query_all_version = """
        SELECT id,acronyms from version
        """
        cur.execute(sql_query_all_version)
        version_rows = cur.fetchall()
        version_list = [
            getBulletinListInVersionReturn(id=row[0], acronyms=row[1], list=[]) for row in version_rows
        ]
        sql_query_bulletin = """
        SELECT bulletin_date,total_leng,order_id FROM bulletin
        WHERE version_id = ?
        """
        for version in version_list:
            cur.execute(sql_query_bulletin, (version.id,))
            bulletin_row = cur.fetchall()
            formatted_data = [
                Bulletin(date=row[0], totalLen=row[1], orderId=row[2]) for row in bulletin_row
            ]
            version.list = formatted_data
        return version_list
    except sqlite3.Error as e:
        return [getBulletinListInVersionReturn(id=-1, acronyms=str(e), list=[])]

@app.get("/getNewBulletin")
def get_new_bulletin():
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
