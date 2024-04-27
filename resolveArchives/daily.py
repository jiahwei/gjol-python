"""
定时执行的脚本
"""
import datetime
import json
from util import get_first_archives,get_notice_info,download_and_resolve_notice
from utilSqlite import get_new_date
from utilType import ArchiveDesc,NoticeInfo
from typing import Union, List, Optional

from testDate import pendingNoticeTest

# 读取存档里已保存的第一条公告
# try:
#     firstNoticeDesc =  get_first_archives()
#     firstNoticeDateStr = firstNoticeDesc.date
#     firstNoticeDate = datetime.datetime.strptime(firstNoticeDateStr,"%Y-%m-%d")
# except:
#     raise ValueError("读取现有的列表失败")

# firstNoticeDateStrFormSqlite = get_new_date()
firstNoticeDateStrFormSqlite = '2023-09-22'
firstNoticeDateFormSqlite = datetime.datetime.strptime(firstNoticeDateStrFormSqlite,"%Y-%m-%d")


def getPath(i):
    url = "http://gjol.wangyuan.com/info/notice{}.shtml"
    if i != 0:
        base_url = url.format(i)
    else:
        base_url = "http://gjol.wangyuan.com/info/notice.shtml"
    return base_url

#读取新一页公告列表，筛选未处理的公告
pendingNotice:List[NoticeInfo] = []
# pendingNotice:List[NoticeInfo] = pendingNoticeTest

for i in range(4):
    if i != 0 :
        url = getPath(i)
        pendingNotice = []
        pendingNotice = get_notice_info(url,firstNoticeDateFormSqlite)
        download_and_resolve_notice(pendingNotice)



# print(pendingNotice[0])
# with open('new-notice.json', 'w') as f:
#     json.dump(allNotice, f,ensure_ascii=False)