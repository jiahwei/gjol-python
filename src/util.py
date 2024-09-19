import json, sqlite3


def creat_table(tableName, SQL_CREATE_TABLE):
    """建表"""
    # SQL_CREATE_TABLE = """CREATE TABLE IF NOT EXISTS bulletin
    #        (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
    #        bulletin_date           TEXT    NOT NULL,
    #        totalLen       INTEGER    NOT NULL,
    #        contentTotalArr  TEXT     NOT NULL);"""
    con = sqlite3.connect(tableName)
    cur = con.cursor()
    cur.execute(SQL_CREATE_TABLE)
    con.commit()
    con.close()


def insert_one(tableName, SQL_INSERT_ONE_DATA, data):
    """新增一条数据"""
    # SQL_INSERT_ONE_DATA = """INSERT INTO bulletin (bulletin_date, totalLen, contentTotalArr)
    #               VALUES (?, ?, ?)"""
    con = sqlite3.connect(tableName)
    cur = con.cursor()
    try:
        cur.execute(SQL_INSERT_ONE_DATA, data)
        con.commit()
        con.close()
    except Exception as e:
        con.rollback()
        print("插入一条记录失败，回滚~")


def insert_many(tableName, SQL_INSERT_MANY_DATA, data):
    """新增多条数据"""
    # SQL_INSERT_MANY_DATA = (
    #     "INSERT INTO bulletin (bulletin_date,totalLen,contentTotalArr) VALUES(?,?,?);"
    # )
    con = sqlite3.connect(tableName)
    cur = con.cursor()
    try:
        cur.executemany(SQL_INSERT_MANY_DATA, data)
        con.commit()
        con.close()
    except Exception as e:
        con.rollback()
        print("插入多条记录失败，回滚")


def query(tableName, SQL_QUERY_DATA):
    con = sqlite3.connect(tableName)
    cur = con.cursor()
    try:
        res =  cur.execute(SQL_QUERY_DATA)
        # fetchone():查询第一条数据
        # fetchall()：查询所有数据
        # fetchmany(1):查询固定的数量的数据
        return res
    except Exception as e:
        print("查询失败")    



creat_table("test.sqlite","""CREATE TABLE IF NOT EXISTS TEST
       (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
       NAME           TEXT    NOT NULL,
       AGE       INTEGER    NOT NULL);""")

# insert_many(
#     "test.sqlite",
#     """INSERT INTO TEST (NAME, AGE)
#                    VALUES (?, ?)""",
#     [
#         ("twwww", "1"),
#         ("tww334w", "1"),
#     ]
# )


con = sqlite3.connect("bulletin.sqlite")
cur = con.cursor()
res = cur.execute("SELECT * FROM bulletin WHERE bulletin_date = ? " , ('2023-09-21',))
print(res.fetchall())
con.commit()
con.close()