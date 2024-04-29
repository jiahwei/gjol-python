import os, json, sqlite3,sys

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
    cursor.execute("SELECT * FROM bulletin ORDER BY DATE DESC LIMIT 1")
    latest_row_date: tuple = cursor.fetchone()
    conn.close()
    json_date = json.loads(latest_row_date[3])
    resolve_date = ArchiveDesc(
        date=latest_row_date[1],
        totalLen=latest_row_date[2],
        contentTotalArr = json_date,
        authors=latest_row_date[4],
        releaseID = latest_row_date[5]
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
    INSERT INTO bulletin (DATE, totalLen, contentTotalArr, NAME)
    VALUES (:date, :totalLen, :contentTotalArr, :name);
    """

    cursor.execute(sql_insert, data)
    conn.commit()
    conn.close()


def sort_sqlit3_by_date(sqlitePath: str = DEFAULT_SQLITE_PATH):
    """按照日期对数据库的数据排序，并替换数据库

    Args:
        sqlitePath (str, optional): _description_. Defaults to DEFAULT_SQLITE_PATH.
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


def check_date_is_thurs(sqlitePath: str = DEFAULT_SQLITE_PATH):
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


def print_table_structure(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for column in columns:
        print(column)
    conn.close()


def update_release_id(sqlitePath: str = DEFAULT_SQLITE_PATH):
    """更新公告表bulletin中的release_id 字段

    Args:
        sqlitePath (str, optional): _description_. Defaults to DEFAULT_SQLITE_PATH.
    """    
    conn = sqlite3.connect(sqlitePath)
    cur = conn.cursor()
    sql_set_release_id = """
    UPDATE bulletin
        SET release_id = (
        SELECT ID FROM release
        WHERE bulletin.date BETWEEN release.startdate AND release.enddate
    );
    """
    cur.execute(sql_set_release_id)
    sql_set_release_id_before_min = """
    UPDATE bulletin
    SET release_id = 1
    WHERE date < (SELECT MIN(startdate) FROM release);
    """
    cur.execute(sql_set_release_id_before_min)
    sql_set_release_id_after_max = """
    UPDATE bulletin
    SET release_id = (SELECT MAX(ID) FROM release)
    WHERE date > (SELECT MAX(enddate) FROM release);
    """
    cur.execute(sql_set_release_id_after_max)    
    conn.commit()
    conn.close()

# id = get_new_date()[5]
# conn = sqlite3.connect(DEFAULT_SQLITE_PATH)
# cur = conn.cursor()
# sql = """
# SELECT DATE,totalLen FROM bulletin
# where release_id = ?
# order by totalLen desc
# """
# cur.execute(sql,(id,))
# records = cur.fetchall()
# conn.close()
# print(records)
