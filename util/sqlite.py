import json
import os
import sqlite3
import sys

from constants import DEFAULT_SQLITE_PATH
from util.type import ArchiveDesc


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

def insert_archive_desc(archive_desc: ArchiveDesc, sqlitePath: str = DEFAULT_SQLITE_PATH):
    """将 ArchiveDesc 对象转换为字典 插入表中

    Args:
        archive_desc (ArchiveDesc): ArchiveDesc 实例
        sqlitePath (str, optional): 数据库路径. Defaults to DEFAULT_SQLITE_PATH.
    """
    conn = sqlite3.connect(sqlitePath)
    cursor = conn.cursor()
    data = archive_desc.model_dump()
    json_data = json.dumps(data["contentTotalArr"])
    data["contentTotalArr"] = json_data
    sql_insert = """
    INSERT INTO bulletin (bulletin_date, totalLen, contentTotalArr, NAME)
    VALUES (:date, :totalLen, :contentTotalArr, :name);
    """

    cursor.execute(sql_insert, data)
    conn.commit()
    conn.close()