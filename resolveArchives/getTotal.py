"""
对archives中存在的公告 desc.josn 进行统计
"""

import os, json, sqlite3
from util import get_default_floder_file
from util import DefalutFloderPath, DefaultTotalPath

def getTotal():
    with open(DefaultTotalPath, "r") as f:
        totalJson = json.load(f)
        f.close()
    return totalJson


def save_descToTotal(info, ignoreSave=True):
    totalInfo = getTotal()
    if ignoreSave and info["date"] in totalInfo["map"]:
        # print("ignoreSave,{}".format(info["date"]))
        return
    totalInfo["list"].append(info)
    totalInfo["map"][info["date"]] = info
    with open(DefaultTotalPath, "w") as f:
        json.dump(totalInfo, f, ensure_ascii=False)
        f.close()

def clean():
    totalInfo={
        "list":[],
        "map":{}
    }
    with open(DefaultTotalPath, "w") as f:
        json.dump(totalInfo, f, ensure_ascii=False)
        f.close()

# clean()

# 获取archives
# floderFiles = get_default_floder_file()
# for floderName in floderFiles:
#     if ".DS_Store" in  floderName:
#         continue
#     descFileName = "{}/{}/desc.json".format(DefalutFloderPath, floderName)
#     if os.path.exists(descFileName):
#         with open(descFileName, "r") as f:
#             content = json.load(f)
#             content.pop('contentArr')
#             content.pop('name')
#             content.pop("authors")            
#             if "date" in content and content['date'] != "":
#                 save_descToTotal(content)
#             else:
#                 content['date'] = floderName
#                 save_descToTotal(content)
#                 # raise Exception("保存失效，缺失必要参数date：{}".format(content))
#             f.close()


# def insert_many(data):
#     """新增多条数据"""
#     SQL_INSERT_MANY_DATA = (
#         "INSERT INTO bulletin (DATE,totalLen,contentTotalArr) VALUES(?,?,?);"
#     )
#     con = sqlite3.connect("bulletin.db")
#     cur = con.cursor()
#     try:
#         cur.executemany(SQL_INSERT_MANY_DATA, data)
#         con.commit()
#     except Exception as e:
#         con.rollback()
#         print("插入多条记录失败，回滚")

# con = sqlite3.connect("bulletin.sqlite")
# cur = con.cursor()
# SQL_CREATE_TABLE = """CREATE TABLE IF NOT EXISTS bulletin
#        (ID INTEGER PRIMARY KEY     AUTOINCREMENT,
#        DATE           TEXT    NOT NULL,
#        totalLen       INTEGER    NOT NULL,
#        contentTotalArr  TEXT     NOT NULL);"""
# cur.execute(SQL_CREATE_TABLE)

# with open(DefaultTotalPath, "r") as f:
#     totalJson = json.load(f)
#     f.close()
# con = sqlite3.connect("bulletin.sqlite")
# cur = con.cursor()
# list = totalJson['list']
# list.reverse()
# for data in list:
#     contentTotalArr = data["contentTotalArr"] if 'contentTotalArr' in data else []
#     json_data = json.dumps(contentTotalArr) 
#     cur.execute(
#         """INSERT INTO bulletin (DATE, totalLen, contentTotalArr)
#                   VALUES (?, ?, ?)""",
#         (data["date"], data["totalLen"], json_data),
#     )
# con.commit()
# con.close()
