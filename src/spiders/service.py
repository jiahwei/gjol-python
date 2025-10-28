"""爬虫服务模块
该模块提供了爬虫服务的相关函数和类。
主要功能包括：
- 下载公告
- 解析公告内容并分类段落
- 检查公告是否已下载
"""

import json
import logging
import random
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from constants import BASEURL, DEFAULT_FLODER_PATH_ABSOLUTE
from src.bulletin.models import BulletinDB
from src.bulletin.schemas import ContentTotal, ParagraphTopic, CHINESE_LABELS
from src.bulletin.service import query_bulletin
from src.bulletin_list.schemas import BulletinType, DownloadBulletin
from src.bulletin_list.models import BulletinList
from src.bulletin_list.service import get_really_bulletin_date, get_bulletin_type
from src.nlp.service import predict_paragraph_category, preprocess_text

logger = logging.getLogger("spiders_test")
daily_logger = logging.getLogger("daily")

header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}


def download_notice(bulletin_info: DownloadBulletin | BulletinList) -> Path | None:
    """下载公告

    Args:
        bulletin_info (DownloadBulletin | BulletinList): 公告信息

    Returns:
        Path | None: content.html的路径
    """

    bulletin_type = get_bulletin_type(bulletin_info.name)
    floder_name = get_really_bulletin_date(bulletin_info)

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
    logger.info("%s,%s,未处理？", bulletin_info.name, bulletin_info.date)
    sleeptime = random.randint(5, 20)
    parent_path.mkdir()
    # 下载公告，保存为source.html
    logger.info("%s,下载公告,%s", bulletin_info.name, time.ctime())
    print(f"{bulletin_info.name},下载公告,{time.ctime()}")
    url = bulletin_info.href.replace("/z/../", BASEURL)
    try:
        res = requests.get(url, headers=header, timeout=30).text
    except requests.Timeout:
        logger.error("请求超时: %s", url)
        raise
    except requests.RequestException as e:
        logger.error("请求失败: %s, 错误: %s", url, str(e))
        raise
    soup = BeautifulSoup(res, "lxml")

    source_file_name = parent_path.joinpath("source.html")
    _ = source_file_name.write_text(str(soup), encoding="utf-8")

    # 过滤不需要的标签,生成content.html
    for excluded_div_name in ["more_button", "bdsharebuttonbox"]:
        excluded_div = soup.find("div", {"class": excluded_div_name})
        if excluded_div is not None:
            _ = excluded_div.extract()
    excluded_tags = soup.select("script")
    for tag in excluded_tags:
        _ = tag.extract()
    details = soup.find("div", class_="details")
    content_file_name = parent_path.joinpath("content.html")
    _ = content_file_name.write_text(str(details), encoding="utf-8")

    logger.info("%s:%s下载完成,等待%s秒", time.ctime(), bulletin_info.name, sleeptime)
    print(f"{time.ctime()}:{bulletin_info.name}下载完成,等待{sleeptime}秒")
    time.sleep(sleeptime)

    return content_file_name


def resolve_notice(
    content_path: Path | None, bulletin_info: DownloadBulletin | BulletinList
) -> BulletinDB | None:
    """解析公告内容并分类段落

    Args:
        content_path (Path | None): 公告content.html的路径
        bulletin_info (DownloadBulletin): 公告信息

    Returns:
        BulletinDB | None: 解析后的公告对象，如果解析失败则返回None
    """
    if content_path is None:
        logger.warning("公告 %s 的content_path为None，无法解析", bulletin_info.name)
        return None

    try:
        # 获取基础公告信息
        base_bulletin: BulletinDB = query_bulletin(bulletin_info=bulletin_info)

        # 读取并解析HTML内容
        content: str = content_path.read_text(encoding="utf-8")
        soup: BeautifulSoup = BeautifulSoup(content, "html5lib")
        details_div = soup.find("div", class_="details")

        if not isinstance(details_div, Tag):
            logger.warning("公告 %s 的details_div为空，规则失效", bulletin_info.name)
            return base_bulletin

        # 提取所有段落
        paragraphs = details_div.find_all("p")
        if not paragraphs:
            logger.warning("公告 %s 未找到段落内容", bulletin_info.name)
            return base_bulletin

        # 按类型分组段落
        category_contents: dict[str, list[str]] = {}  # 类型 -> 内容列表
        category_lengths: dict[str, int] = {}  # 类型 -> 总长度

        # 处理每个段落
        for p in paragraphs:
            p_text: str = p.text.strip()
            if not p_text:
                continue

            words = preprocess_text(p_text)
            if words.strip():
                category = predict_paragraph_category(words)
                logger.debug("段落分类: %s... -> %s", p_text[:30], category)

                # 将段落添加到对应类型
                if category not in category_contents:
                    category_contents[category] = []
                    category_lengths[category] = 0

                category_contents[category].append(p_text)
                category_lengths[category] += len(p_text)

        # 如果没有有效内容，返回基础公告
        if not category_contents:
            logger.warning("公告 %s 没有有效内容可分类", bulletin_info.name)
            return base_bulletin

        # 构建内容数组
        content_total_arr: list[ContentTotal] = []
        total_leng: int = 0

        for category, contents in category_contents.items():
            content_item = ContentTotal(
                type=CHINESE_LABELS[ParagraphTopic(category)],
                leng=category_lengths[category],
                content=contents,
            )
            total_leng += category_lengths[category]
            content_total_arr.append(content_item)

        # 更新公告信息
        content_total_json = json.dumps(
            [item.model_dump() for item in content_total_arr], ensure_ascii=False
        )
        base_bulletin.content_total_arr = content_total_json
        base_bulletin.total_leng = total_leng

        logger.info(
            "公告 %s 解析完成，共 %d 种类型，总长度 %d",
            bulletin_info.name,
            len(content_total_arr),
            total_leng,
        )
        return base_bulletin

    except Exception as e:
        logger.error("解析公告 %s 时发生错误: %s", bulletin_info.name, str(e))
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
    if bulletin_path.exists() and bulletin_path.is_dir():
        # 检查 source.html 和 content.html 文件是否存在
        source_file = bulletin_path.joinpath("source.html")
        content_file = bulletin_path.joinpath("content.html")
        return source_file.exists() and content_file.exists()

    return False
