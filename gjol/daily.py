"""
定时执行的脚本
"""
import datetime
import json
from util import getFirstArchives,getNoticeInfo

# 读取已保存的第一条公告
try:
    firstNoticeDesc=getFirstArchives()
    firstNoticeDateStr = firstNoticeDesc['date']
    firstNoticeDate = datetime.datetime.strptime(firstNoticeDateStr,"%Y-%m-%d")
except:
    raise ValueError("读取现有的列表失败")


def getPath(i):
    url = "http://gjol.wangyuan.com/info/notice{}.shtml"
    if i != 0:
        base_url = url.format(i)
    else:
        base_url = "http://gjol.wangyuan.com/info/notice.shtml"
    return base_url

#读取新一页公告列表，筛选未处理的公告
pendingNotice = []
for i in range(1):
    url = getPath(i)
    getNoticeInfo(url,firstNoticeDate)

# with open('new-notice.json', 'w') as f:
#     json.dump(allNotice, f,ensure_ascii=False)
