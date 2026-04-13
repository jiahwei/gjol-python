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
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Tag

from constants import BASEURL, DEFAULT_FLODER_PATH_ABSOLUTE
from src.bulletin.models import BulletinDB
from src.bulletin.schemas import ContentTotal,ParagraphTopic
from src.bulletin.service import query_bulletin
from src.bulletin_list.schemas import BulletinType, DownloadBulletin
from src.bulletin_list.models import BulletinList
from src.bulletin_list.service import get_really_bulletin_date, get_bulletin_type
from src.nlp.service import (
    predict_paragraph_category,
    predict_paragraphs_category_ollama,
    preprocess_text,
)

logger = logging.getLogger("spiders_test")
daily_logger = logging.getLogger("daily")

header = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
    )
}

_FORMAT_PREFIXES = ("各位仙家弟子", "亲爱的仙家弟子", "诸位仙家弟子")
_FORMAT_PHRASES = ("敬请谅解", "祝大家游戏愉快", "项目组")
_CONTEXT_CATEGORIES = {
    ParagraphTopic.STORE.value,
    ParagraphTopic.PVX.value,
    ParagraphTopic.PVE.value,
    ParagraphTopic.PVP.value,
}
_ACTIVITY_OR_STORE_ITEM_KEYWORDS = (
    "活动",
    "节日",
    "奖励",
    "兑换",
    "限量商品",
    "不限量商品",
    "挂件",
    "头像",
    "头像框",
    "外装",
    "时装",
    "商人",
    "传送特效",
)
_SKILL_FALSE_POSITIVE_KEYWORDS = ("技能面板", "外装技能", "传送技能", "传送特效")


def _is_format_paragraph(text: str) -> bool:
    """判断是否为公告开头/结尾的格式化文本。"""
    stripped_text = text.strip()
    if stripped_text.startswith(_FORMAT_PREFIXES):
        return True
    if re.fullmatch(r"\d{4}年\d{1,2}月\d{1,2}日", stripped_text):
        return True
    return any(phrase in stripped_text for phrase in _FORMAT_PHRASES)


def _find_nearby_context_category(categories: list[str], index: int) -> str | None:
    """查找当前段落附近最近的强语义上下文分类。"""
    for left_index in range(index - 1, -1, -1):
        if categories[left_index] in _CONTEXT_CATEGORIES:
            return categories[left_index]
    for right_index in range(index + 1, len(categories)):
        if categories[right_index] in _CONTEXT_CATEGORIES:
            return categories[right_index]
    return None


def _looks_like_activity_or_store_item(text: str) -> bool:
    """判断文本是否更像活动/商城区块里的附属条目。"""
    return any(keyword in text for keyword in _ACTIVITY_OR_STORE_ITEM_KEYWORDS)


def _postprocess_ollama_categories(valid_texts: list[str], categories: list[str]) -> list[str]:
    """对 LLM 分类结果做少量确定性修正。"""
    fixed_categories = categories.copy()
    for i, text in enumerate(valid_texts):
        if _is_format_paragraph(text):
            fixed_categories[i] = ParagraphTopic.FORMAT.value
            continue

        if fixed_categories[i] != ParagraphTopic.SKILL.value:
            continue

        has_skill_false_positive = any(
            keyword in text for keyword in _SKILL_FALSE_POSITIVE_KEYWORDS
        )
        if not has_skill_false_positive and not _looks_like_activity_or_store_item(text):
            continue

        nearby_context = _find_nearby_context_category(fixed_categories, i)
        if nearby_context in {
            ParagraphTopic.PVX.value,
            ParagraphTopic.STORE.value,
        }:
            logger.debug(
                "修正职业调整误判: %s -> %s",
                text[:30],
                nearby_context,
            )
            fixed_categories[i] = nearby_context
    return fixed_categories



def download_notice(bulletin_info: DownloadBulletin | BulletinList) -> Path | None:
    """下载公告内容,生成content.html和source.html

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
        return parent_path.joinpath("content.html")
    logger.info("%s,%s,未处理？", bulletin_info.name, bulletin_info.date)
    sleeptime = random.randint(5, 20)
    parent_path.mkdir()
    # 下载公告，保存为source.html
    logger.info("%s,下载公告,%s", bulletin_info.name, time.ctime())
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
    time.sleep(sleeptime)

    return content_file_name

def _resolve_paragraphs(soup: BeautifulSoup, use_ollama: bool = False):
    """分类段落
    """
    details_div = soup.find("div", class_="details")
    if not isinstance(details_div, Tag):
        raise ValueError("details_div 不是 Tag 类型")
    paragraphs = details_div.find_all("p")
    if not paragraphs:
        raise ValueError("公告未找到段落内容")

    category_contents: dict[str, list[str]] = {}
    category_lengths: dict[str, int] = {}

    valid_texts: list[str] = []
    valid_words: list[str] = []

    # 收集有效段落
    for p in paragraphs:
        p_text: str = p.text.strip()
        if not p_text:
            continue

        words = preprocess_text(p_text)
        if words.strip():
            valid_texts.append(p_text)
            valid_words.append(words)

    if not valid_texts:
        return category_contents, category_lengths

    # 批量预测类别
    if use_ollama:
        categories = predict_paragraphs_category_ollama(valid_texts)
        categories = _postprocess_ollama_categories(valid_texts, categories)
        # 本地再加两层保险：
        # 1. 修正“无更新”误判
        for i, (text, cat) in enumerate(zip(valid_texts, categories)):
            if cat == "无更新" and "无更新" not in text:
                logger.debug("修正模型误判的无更新: %s", text[:30])
                categories[i] = "格式"

    else:
        categories = [predict_paragraph_category(w) for w in valid_words]

    # 组装结果
    for p_text, category in zip(valid_texts, categories):
        logger.debug("段落分类: %s... -> %s", p_text[:30], category)

        # 将段落添加到对应类型
        if category not in category_contents:
            category_contents[category] = []
            category_lengths[category] = 0

        category_contents[category].append(p_text)
        category_lengths[category] += len(p_text)

    return category_contents, category_lengths



def resolve_notice(
    content_path: Path | None,
    bulletin_info: DownloadBulletin | BulletinList,
    use_ollama: bool = False,
) -> BulletinDB | None:
    """解析公告内容并分类段落

    Args:
        content_path (Path | None): 公告content.html的路径
        bulletin_info (DownloadBulletin): 公告信息
        use_ollama (bool, optional): 是否使用 Ollama 模型分类. Defaults to False.

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
        try:
            category_contents, category_lengths = _resolve_paragraphs(
                soup, use_ollama=use_ollama
            )
        except ValueError as e:
            logger.warning("公告 %s 解析段落时出错: %s", bulletin_info.name, str(e))
            return base_bulletin

        # 构建内容数组
        content_total_arr: list[ContentTotal] = []
        total_leng: int = 0

        for category, contents in category_contents.items():
            content_item = ContentTotal(
                type=ParagraphTopic(category),
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
