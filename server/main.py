from typing import Union, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel, Field
from datetime import date
import json, sqlite3,sys
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
        if payload.start_date and payload.end_date:
            c.execute(
                "SELECT DATE,TOTALLEN FROM bulletin WHERE DATE BETWEEN ? AND ?",
                (payload.start_date, payload.end_date),
            )
        elif payload.start_date:
            c.execute(
                "SELECT DATE,TOTALLEN FROM bulletin WHERE DATE = ?",
                (payload.start_date,),
            )
        rows = c.fetchall()
        conn.close()

        # 数据处理
        result = [{"date": row[0], "totalLen": row[1]} for row in rows]

        return result
    except sqlite3.Error as e:
        return {"error": str(e)}


@app.post("/getNewBulletin")
def get_new_bulletin():
    info:ArchiveDesc = get_new_date()
    con = sqlite3.connect(DEFAULT_SQLITE_PATH)
    try:
        cur = con.cursor()
        sql_query_release = """
        SELECT acronyms from release where id = ?
        """
        cur.execute(sql_query_release,(info.releaseID,))
        rows = cur.fetchone()
        con.close()

        result = info.model_dump()
        result['reselseName'] = rows[0]
        return result
    except sqlite3.Error as e:
        return {"error": str(e)}
