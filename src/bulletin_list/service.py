import requests 
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
from sqlmodel import Session, select, and_, desc
from typing import List


from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import DownloadBulletin

header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}

def get_list_url(i: int) -> str:
    """返回公告列表的URL

    Args:
        i (int): 第几页

    Returns:
        str: 公告列表的URL
    """
    url = "http://gjol.wangyuan.com/info/notice{}.shtml"
    if i != 0:
        base_url = url.format(i)
    else:
        base_url = "http://gjol.wangyuan.com/info/notice.shtml"
    return base_url


def get_bulletin_list(
    url: str, first_date_str: str | None
) -> List[DownloadBulletin]:
    """获取要下载的公告列表

    Args:
        url (str): 公告列表的URL
        first_date_str (str | None): 数据库中最新一条公告的日期

    Returns:
        List[DownloadBulletin]: 公告列表
    """

    res = requests.get(url, headers=header).text
    soup = BeautifulSoup(res, "lxml")
    allList = soup.find("div", class_="list_box").find_all("li")  # type: ignore
    resList: List[DownloadBulletin] = []
    if first_date_str is not None:
        firstNoticeDate = datetime.strptime(first_date_str, "%Y-%m-%d")
    for li in allList:
        infoForA = li.a
        infoForTime = li.span
        date = datetime.strptime(infoForTime.string, "%Y-%m-%d")
        if date > firstNoticeDate or first_date_str is None:
            info = DownloadBulletin(
                name=infoForA.attrs["title"],
                href=infoForA.attrs["href"],
                date=infoForTime.string,
            )
            resList.append(info)
        else:
            print(infoForA.attrs["title"])
    return resList