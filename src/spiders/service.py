import os, shutil, json, requests, re, warnings, time, random, sqlite3, sys
from pathlib import Path
from datetime import date, datetime, timedelta
from lxml import etree, html
from bs4 import BeautifulSoup, Tag
from typing import Union, List, Optional

from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.service import get_bulletin_date,get_bulletin_type
from src.bulletin_list.schemas import BulletinType
from src.bulletin.models import Bulletin
from src.bulletin.schemas import ContentTotal
from src.version.service import get_version_info_by_bulletin_date
from src.version.schemas import VersionInfo


from constants import DEFAULT_SQLITE_PATH, BASEURL, DEFAULT_FLODER_PATH_ABSOLUTE

import logging

loggig_path = Path("src").joinpath("spiders").joinpath("test.log")
logging.basicConfig(
    filename=loggig_path,
    filemode="a",
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)

header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}


def download_notice(bulletin_info: DownloadBulletin) -> Optional[Path]:
    """下载公告

    Args:
        bulletin_info (DownloadBulletin): 公告信息

    Returns:
        Path | None: content.html的路径
    """
    bulletin_type = get_bulletin_type(bulletin_info.name)
    floder_name = bulletin_info.date

    if bulletin_type in {BulletinType.CIRCULAR, BulletinType.OTHER}:
        logging.info(f"{bulletin_info.name},不是公告，不需要处理,跳过,{time.ctime()}")
        return None

    is_bulletin_download = check_bulletin_download(floder_name, bulletin_type)
    parent_path = (
        Path(DEFAULT_FLODER_PATH_ABSOLUTE)
        .joinpath(bulletin_type.value)
        .joinpath(floder_name)
    )
    if is_bulletin_download:
        # 该公告已经下载过
        logging.info(f"{bulletin_info.name},已经下载过了,{time.ctime()}")
        return parent_path.joinpath("content.html")
    logging.info(f"{bulletin_info.name},未处理？")
    return None
    sleeptime = random.randint(5, 20)
    parent_path.mkdir()
    # 下载公告，保存为source.html
    logging.info(f"{bulletin_info.name},下载公告,{time.ctime()}")
    print(f"{bulletin_info.name},下载公告,{time.ctime()}")
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

    logging.info(f"{time.ctime()}:{bulletin_info.name}下载完成,等待{sleeptime}秒")
    print(f"{time.ctime()}:{bulletin_info.name}下载完成,等待{sleeptime}秒")
    time.sleep(sleeptime)

    return content_file_name


def get_base_bulletin(
    content_path: Optional[Path], bulletin_info: DownloadBulletin
) -> Bulletin:
    info = {
        "bulletin_date": get_bulletin_date(bulletin_info),
        "total_leng": 0,
        "content_total_arr": "",
        "bulletin_name": bulletin_info.name,
        "version_id": None,
        "rank_id": 0,
        "type": get_bulletin_type(bulletin_info.name),
    }
    return Bulletin(**info)


def resolve_notice(
    content_path: Optional[Path], bulletin_info: DownloadBulletin
) -> Bulletin | None:
    if content_path is None:
        logging.warning("content_path is None")
        return None
    base_bulletin = get_base_bulletin(content_path, bulletin_info)
    content = content_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html5lib")
    details_div = soup.find("div", class_="details")
    if not isinstance(details_div, Tag):
        logging.warning("details_div为空，规则失效")
        return base_bulletin
    paragraphs = details_div.find_all("p")
    target_text = "本次例行停机维护，无更新内容！"
    no_update: bool = False
    for p in paragraphs:
        if target_text in p.text:
            no_update = True
            break
    if no_update:
        # 无更新
        base_bulletin.total_leng = len(target_text)
        resolve_bulletin = Bulletin(**base_bulletin.model_dump())
        return resolve_bulletin
    # 有更新内容
    logging.info("有更新内容")
    all_details_text = details_div.get_text()
    markers = ["本次维护更新内容如下：", "维护期间给您带来的不便，敬请谅解！"]
    extracted_content = extract_between_markers(all_details_text, markers)
    if extracted_content is None:
        logging.error(f"{bulletin_info.name}，resolve_notice失败")
        return None
    # logging.info("extracted_content")
    # logging.info(extracted_content)
    content_total_arr = extract_bulletin_contents(extracted_content)
    # logging.info("content_total_arr")
    # logging.info(content_total_arr)
    base_bulletin.total_leng = len(extracted_content)
    base_bulletin.content_total_arr = json.dumps(content_total_arr)
    version_info = get_version_info_by_bulletin_date(base_bulletin.bulletin_date,base_bulletin.total_leng)
    if version_info is None:
        logging.error(f"{bulletin_info.name}，version_info失败")
        return None
    base_bulletin.version_id = version_info.version_id
    base_bulletin.rank_id = version_info.rank
    resolve_bulletin = Bulletin(**base_bulletin.model_dump())
    return resolve_bulletin
    



def extract_between_markers(text: str, markers: list) -> str | None:
    start_marker, end_marker = markers
    start_index = text.find(start_marker)
    end_index = text.find(end_marker, start_index)

    if start_index != -1 and end_index != -1:
        start_index += len(start_marker)
        return text[start_index:end_index].strip()
    else:
        logging.error("extract_between_markers:切割失败")
        return None


def extract_bulletin_contents(text: str) -> List[ContentTotal]:
    segments = text.split("☆")
    bulletins = []

    for segment in segments:
        lines = segment.strip().split("\n")
        if len(lines) > 1:
            name = lines[0].strip()
            content = "\n".join(line.strip() for line in lines[1:])
            content_leng = len(content)
            bulletin = ContentTotal(name=name, leng=content_leng)
            bulletins.append(bulletin.model_dump())
    return bulletins


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
