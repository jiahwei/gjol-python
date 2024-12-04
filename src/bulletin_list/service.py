import requests, time, random, re
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup
from sqlmodel import Session, select, and_, desc
from typing import List

from src.database import get_session, engine
from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import DownloadBulletin,BulletinType

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
        bulletin_type = get_bulletin_type(info.name)
        new_bulletin = BulletinList(name=info.name, href=info.href, date=info.date ,type=bulletin_type.value)
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


def get_bulletin_type(bulletin_name: str) -> BulletinType:
    """返回公告类型

    Args:
        bulletin_name (str): 公告名称

    Returns:
        BulletinType | None: 公告类型或 None
    """
    if ("职业" in bulletin_name or "技能" in bulletin_name) and '《古剑奇谭网络版》' in bulletin_name:
        return BulletinType.SKILL
    if ("资料片" in bulletin_name or "版本" in bulletin_name) and '更新' in bulletin_name and '公告' in bulletin_name:
        return BulletinType.VERSION
    if "更新维护公告" in bulletin_name:
        return BulletinType.ROUTINE
    if "通告" in bulletin_name:
        return BulletinType.CIRCULAR
    return BulletinType.OTHER


def get_really_bulletin_date(bulletin_info: BulletinList) -> str:
    """公告列表中的日期多数是周三，处理成周四。因为bulletins文件夹中使用更新日（周四）作为文件名

    Args:
        bulletin_info (BulletinList): _description_

    Returns:
        str: 处理后的日期
    """
    # 混沌初开，没什么规律，直接跳过
    filter_list = ['2018-07-07','2018-07-10']
    if bulletin_info.date in filter_list:
        return bulletin_info.date
    
    date_obj = datetime.strptime(bulletin_info.date, '%Y-%m-%d')
    week_day = date_obj.weekday()

    # 如果日期是周一至周三，调整到当周的周四
    if week_day in {0, 1, 2}:  # 周一到周三
        days_to_add = 3 - week_day
        date_obj += timedelta(days=days_to_add)
    elif week_day in {4, 5, 6}:  # 周五到周日
        days_to_add = 10 - week_day  # 调整到下周四
        date_obj += timedelta(days=days_to_add)

    # 返回处理后的日期
    return date_obj.strftime('%Y-%m-%d')
