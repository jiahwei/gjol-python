from typing import Union, List, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import date
import json, sqlite3


app = FastAPI()


class Content(BaseModel):
    name: str
    leng: int
    content: str


class Bulletin(BaseModel):
    date: str
    total_len: int
    content_total_arr: List[Content] = []


class DatePayload(BaseModel):
    start_date: Optional[date]
    end_date: Optional[date]
    # show_all_info: bool = False


@app.post("/getBulletinByDate")
def get_bulletin_by_date(payload: DatePayload):
    conn = sqlite3.connect("../sqlite/bulletin.sqlite")
    try:
        c = conn.cursor()
        if payload.start_date and payload.end_date:
            c.execute(
                "SELECT DATE,TOTALLEN FROM bulletin WHERE DATE BETWEEN ? AND ?",
                (payload.start_date, payload.end_date),
            )
        elif payload.start_date:
            c.execute("SELECT DATE,TOTALLEN FROM bulletin WHERE DATE = ?", (payload.start_date,))
        rows = c.fetchall()
        conn.close()

        # 数据处理
        result = [{"date": row[0], "totalLen": row[1]} for row in rows]

        return  result
    except sqlite3.Error as e:
        return {"error": str(e)}
