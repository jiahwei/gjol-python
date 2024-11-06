import os, shutil, json, datetime, requests, re, warnings, time, random, sqlite3, sys
from pathlib import Path
from datetime import date, datetime, timedelta
from lxml import etree, html
from bs4 import BeautifulSoup
from typing import Union, List, Optional

from src.spiders.schemas import DownloadBulletin, BulletinType
from constants import DEFAULT_SQLITE_PATH, BASEURL, DEFAULT_FLODER_PATH_ABSOLUTE


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


def get_download_bulletin_list(
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


def download_notice(bulletin_info: DownloadBulletin):
    bulletin_type = get_bulletin_type(bulletin_info.name)
    floder_name = bulletin_info.date

    if bulletin_type is None:
        print(f"{bulletin_info.name},不是公告，不需要处理,跳过,{time.ctime()}")
        return None

    is_bulletin_download = check_bulletin_download(floder_name, bulletin_type)
    parent_path = (
        Path(DEFAULT_FLODER_PATH_ABSOLUTE)
        .joinpath(bulletin_type.value)
        .joinpath(floder_name)
    )
    if is_bulletin_download:
        # 该公告已经下载过
        return parent_path.joinpath("content.html")
    sleeptime = random.randint(10, 40)
    # 创建文件夹
    parent_path.mkdir()
    # 下载公告，保存为source.html
    url = bulletin_info.href.replace("/z/../", BASEURL)
    res = requests.get(url, headers=header).text
    soup = BeautifulSoup(res, "lxml")

    source_file_name = parent_path.joinpath("source.html")
    source_file_name.write_text(str(soup))

    # 过滤不需要的标签,生成content.html
    for excludedDivName in ["more_button", "bdsharebuttonbox"]:
        excluded_div = soup.find("div", {"class": excludedDivName})
        if excluded_div is not None:
            excluded_div.extract()
    excluded_tags = soup.select("script")
    for tag in excluded_tags:
        tag.extract()
    details = soup.find("div", class_="details")
    content_file_name = parent_path.joinpath("content.html")
    content_file_name.write_text(str(details))

    print(f"{time.ctime()}:{bulletin_info.name}下载完成,等待{sleeptime}秒")
    time.sleep(sleeptime)

    return content_file_name


def get_bulletin_type(bulletin_name: str) -> Optional[BulletinType]:
    """返回公告类型

    Args:
        bulletin_name (str): 公告名称

    Returns:
        BulletinType | None: 公告类型或None
    """
    is_routine_update = "更新维护公告" in bulletin_name
    is_version_update = "资料片" in bulletin_name or "版本" in bulletin_name
    is_skill_change = (
        "职业调整公告" in bulletin_name or "职业技能改动公告" in bulletin_name
    )
    if is_skill_change:
        return BulletinType.SKILL
    elif is_version_update:
        return BulletinType.VERSION
    elif is_routine_update:
        return BulletinType.ROUTINE
    else:
        return None


def check_bulletin_download(folder_date: str, bulletin_type: BulletinType) -> bool:
    """公告是否已下载

    Args:
        folder_date (str): 日期（文件夹名称）
        bulletin_type (BulletinType): 日期（文件夹名称）

    Returns:
        bool: 如果文件存在，返回 True；否则返回 False
    """
    parent_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath(bulletin_type.value)
    bulletin_path = parent_path.joinpath(folder_date)
    return bulletin_path.exists() and bulletin_path.is_dir()
