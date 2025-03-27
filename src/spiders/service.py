import os, shutil, json, requests, re, warnings, time, random, sqlite3, sys
from pathlib import Path
from datetime import date, datetime, timedelta
from bs4 import BeautifulSoup, Tag

from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.service import get_bulletin_date, get_bulletin_type
from src.bulletin_list.schemas import BulletinType
from src.bulletin.models import BulletinDB
from src.bulletin.schemas import ContentTotal,ParagraphTopic
from src.nlp.service import preprocess_text, predict_paragraph_category

from constants import DEFAULT_SQLITE_PATH, BASEURL, DEFAULT_FLODER_PATH_ABSOLUTE

import logging

logger = logging.getLogger("spiders_test")

header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}


def download_notice(bulletin_info: DownloadBulletin) -> Path | None:
    """下载公告

    Args:
        bulletin_info (DownloadBulletin): 公告信息

    Returns:
        Path | None: content.html的路径
    """
    bulletin_type = get_bulletin_type(bulletin_info.name)
    floder_name = bulletin_info.date

    if bulletin_type in {BulletinType.CIRCULAR, BulletinType.OTHER}:
        # logger.info(f"{bulletin_info.name},不是公告，不需要处理,跳过,{time.ctime()}")
        return None

    is_bulletin_download = check_bulletin_download(floder_name, bulletin_type)
    parent_path = (
        Path(DEFAULT_FLODER_PATH_ABSOLUTE)
        .joinpath(bulletin_type.value)
        .joinpath(floder_name)
    )
    if is_bulletin_download:
        # 该公告已经下载过
        # logger.info(f"{bulletin_info.name},已经下载过了,{time.ctime()}")
        return parent_path.joinpath("content.html")
    logger.info(f"{bulletin_info.name},{bulletin_info.date},未处理？")
    sleeptime = random.randint(5, 20)
    parent_path.mkdir()
    # 下载公告，保存为source.html
    logger.info(f"{bulletin_info.name},下载公告,{time.ctime()}")
    print(f"{bulletin_info.name},下载公告,{time.ctime()}")
    url = bulletin_info.href.replace("/z/../", BASEURL)
    res = requests.get(url, headers=header).text
    soup = BeautifulSoup(res, "lxml")

    source_file_name = parent_path.joinpath("source.html")
    source_file_name.write_text(str(soup), encoding="utf-8")

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
    content_file_name.write_text(str(details), encoding="utf-8")

    logger.info(f"{time.ctime()}:{bulletin_info.name}下载完成,等待{sleeptime}秒")
    print(f"{time.ctime()}:{bulletin_info.name}下载完成,等待{sleeptime}秒")
    time.sleep(sleeptime)

    return content_file_name


def get_base_bulletin(
    content_path: Path | None, bulletin_info: DownloadBulletin
) -> BulletinDB:
    info = {
        "bulletin_date": get_bulletin_date(bulletin_info),
        "total_leng": 0,
        "content_total_arr": "",
        "bulletin_name": bulletin_info.name,
        "version_id": None,
        "rank_id": 0,
        "type": get_bulletin_type(bulletin_info.name).value,
    }
    return BulletinDB(**info)


def resolve_notice(
    content_path: Path | None, bulletin_info: DownloadBulletin
) -> BulletinDB | None:
    """解析公告

    Args:
        content_path (Path | None): 公告content.html的路径
        bulletin_info (DownloadBulletin): 公告信息

    Returns:
        BulletinDB | None: 解析后的公告
    """    
    if content_path is None:
        logger.warning("content_path is None")
        return None
    base_bulletin = get_base_bulletin(content_path, bulletin_info)
    content = content_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(content, "html5lib")
    details_div = soup.find("div", class_="details")
    if not isinstance(details_div, Tag):
        logger.warning("details_div为空，规则失效")
        return base_bulletin
    paragraphs = details_div.find_all("p")
    # 按类型分组段落
    category_contents = {}  # 类型 -> 内容列表
    category_lengths = {}   # 类型 -> 总长度
    
    for p in paragraphs:
        p_text = p.text
        words = preprocess_text(p_text)
        if words.strip():
            category = predict_paragraph_category(words)
            logger.info(f"{p_text},段落类型：{category}")
            
            # 将段落添加到对应类型
            if category not in category_contents:
                category_contents[category] = []
                category_lengths[category] = 0
            
            category_contents[category].append(p_text)
            category_lengths[category] += len(p_text)
    

    content_total_arr:list[ContentTotal] = []
    for category, contents in category_contents.items():
        content_item = ContentTotal(
            type=ParagraphTopic(category),
            leng=category_lengths[category],
            content=contents
        )
        content_total_arr.append(content_item)
    
    
    content_total_json = json.dumps([item.model_dump() for item in content_total_arr], ensure_ascii=False)
    base_bulletin.content_total_arr = content_total_json

    return base_bulletin    


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
    if bulletin_path.exists() and bulletin_path.is_dir():
        # 检查 source.html 和 content.html 文件是否存在
        source_file = bulletin_path.joinpath("source.html")
        content_file = bulletin_path.joinpath("content.html")
        return source_file.exists() and content_file.exists()

    return False
