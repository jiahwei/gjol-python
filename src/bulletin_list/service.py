import requests, time, random, re
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
from sqlmodel import Session, select, and_, desc
from typing import List

from src.database import get_session, engine
from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import DownloadBulletin

header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}


def get_list_url(i: int = 0) -> str:
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


def get_bulletin_list(url: str, first_date_str: str | None) -> List[DownloadBulletin]:
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
        info = DownloadBulletin(
            name=infoForA.attrs["title"],
            href=infoForA.attrs["href"],
            date=infoForTime.string,
        )
        update_bulletin_list(info=info)
        if date > firstNoticeDate or first_date_str is None:
            resList.append(info)
        else:
            print(infoForA.attrs["title"])
    return resList


def download_bulletin_list(
    first_date_str: str | None, pageNum: int = 1
) -> List[DownloadBulletin]:
    """下载公告列表

    Args:
        first_date_str (str | None): 数据库中最新一条公告的日期
        pageNum (int, optional): 下载几页公告. Defaults to 1.

    Returns:
        List[DownloadBulletin]: 公告列表
    """
    bulletin_list: List[DownloadBulletin] = []
    for i in range(pageNum):
        url = get_list_url(i)
        new_list = get_bulletin_list(url, first_date_str)
        bulletin_list.extend(new_list)
    return bulletin_list


def download_all_list(url: str):
    res = requests.get(url, headers=header).text
    soup = BeautifulSoup(res, "lxml")
    allList = soup.find("div", class_="list_box").find_all("li")  # type: ignore
    resList: List[DownloadBulletin] = []
    for li in allList:
        infoForA = li.a
        infoForTime = li.span
        date = datetime.strptime(infoForTime.string, "%Y-%m-%d")
        info = DownloadBulletin(
            name=infoForA.attrs["title"],
            href=infoForA.attrs["href"],
            date=infoForTime.string,
        )
        update_bulletin_list(info=info)
    sleeptime = random.randint(1, 10)
    print(f"{time.ctime()}:{url}下载完成,等待{sleeptime}秒")
    time.sleep(sleeptime)


def update_bulletin_list(info: DownloadBulletin):
    with Session(engine) as session:
        new_bulletin = BulletinList(name=info.name, href=info.href, date=info.date)
        try:
            session.add(new_bulletin)
            session.commit()
            print("插入新数据成功")
        except:
            session.rollback()
            print("数据已存在，不执行插入")


def get_new_date() -> str | None:
    """查询数据库bulletin_list中最新一条公告的日期"""
    with Session(engine) as session:
        statement = select(BulletinList.date).order_by(desc(BulletinList.date)).limit(1)
        result = session.exec(statement)
        first_result = result.first()
        return first_result


def get_bulletin_date(bulletin_info: DownloadBulletin) -> str:
    year_month = bulletin_info.date[:-3]
    match = re.search(r"(\d+)月(\d+)日", bulletin_info.name)
    day = "01" if match is None else match.group(2)
    date = f"{year_month}-{day}"
    resolve_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    return resolve_date
