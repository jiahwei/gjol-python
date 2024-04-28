# from util import get_first_archives, get_notice_info
from utilType import ArchiveDesc
import os, json, sqlite3

DefaultSqlitePath = "./sqlite/bulletin.sqlite"


def get_new_date(sqlitePath: str = DefaultSqlitePath):
    """取最新日期的一条数据
    Args:
        sqlitePath(str):数据库路径
    Returns:
        str:数据库中最新一条公告的日期
    """
    conn = sqlite3.connect(sqlitePath)
    cursor = conn.cursor()
    # 查询最新日期的一条数据
    cursor.execute("SELECT DATE FROM bulletin ORDER BY DATE DESC LIMIT 1")
    latest_row_date: tuple = cursor.fetchone()
    conn.close()
    return latest_row_date[0]


def insert_archive_desc(archive_desc: ArchiveDesc, sqlitePath: str = DefaultSqlitePath):
    """将 ArchiveDesc 对象转换为字典 插入表中

    Args:
        archive_desc (ArchiveDesc): ArchiveDesc 实例
        sqlitePath (str, optional): 数据库路径. Defaults to DefaultSqlitePath.
    """
    conn = sqlite3.connect(sqlitePath)
    cursor = conn.cursor()
    data = archive_desc.model_dump()
    json_data = json.dumps(data["contentTotalArr"])
    data["contentTotalArr"] = json_data
    sql_insert = """
    INSERT INTO bulletin (DATE, totalLen, contentTotalArr, NAME)
    VALUES (:date, :totalLen, :contentTotalArr, :name);
    """

    cursor.execute(sql_insert, data)
    conn.commit()
    conn.close()


def sort_sqlit3_by_date(sqlitePath: str = DefaultSqlitePath):
    """按照日期对数据库的数据排序，并替换数据库

    Args:
        sqlitePath (str, optional): _description_. Defaults to DefaultSqlitePath.
    """
    conn = sqlite3.connect(sqlitePath)
    cursor = conn.cursor()
    # 创建一个新的表
    sql_create_new_table = """
    CREATE TABLE IF NOT EXISTS bulletin_sorted
        (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
        DATE           TEXT    NOT NULL,
        totalLen       INTEGER    NOT NULL,
        contentTotalArr  TEXT     NOT NULL,
        NAME           TEXT);
    """
    cursor.execute(sql_create_new_table)

    # 将按日期正序排列的数据插入到新的表中
    sql_insert_sorted_data = """
    INSERT INTO bulletin_sorted (DATE, totalLen, contentTotalArr, NAME)
    SELECT DATE, totalLen, contentTotalArr, NAME FROM bulletin ORDER BY DATE ASC;
    """
    cursor.execute(sql_insert_sorted_data)
    conn.commit()

    # 如果你想删除原来的表并将新的表重命名为 bulletin，你可以使用以下语句：
    sql_drop_old_table = "DROP TABLE bulletin;"
    cursor.execute(sql_drop_old_table)
    sql_rename_new_table = "ALTER TABLE bulletin_sorted RENAME TO bulletin;"
    cursor.execute(sql_rename_new_table)
    conn.commit()


def check_date_is_thurs(sqlitePath: str = DefaultSqlitePath):
    conn = sqlite3.connect(sqlitePath)
    cursor = conn.cursor()
    sql_query_is_thurs = """
    SELECT DATE
    FROM bulletin
    WHERE STRFTIME('%w', DATE) != '4';
    """
    cursor.execute(sql_query_is_thurs)
    results = cursor.fetchall()
    conn.close()
    return results
