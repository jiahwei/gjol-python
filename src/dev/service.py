"""开发测试模块中的通用方法
"""
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag
from sqlmodel import Session, select

from constants import DEFAULT_FLODER_PATH_ABSOLUTE
from src.bulletin.models import BulletinDB
from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import BulletinType, DownloadBulletin
from src.bulletin_list.service import get_bulletin_type
from src.database import engine
from src.spiders.service import download_notice, resolve_notice

logger = logging.getLogger("nlp_test")
daily_logger = logging.getLogger("daily")

def run_preprocess_task(
    test_date: str | None = None,
    use_lm_studio: bool = False,
    save_json: bool = False,
    target_name: str | None = None,
) -> list[BulletinDB]:
    """下载并解析公告数据。

    如果传入日期，只处理该日期的公告；如果不传日期，则处理全部公告。

    Args:
        test_date: 指定要处理的公告日期；为空时处理全部公告。
        use_lm_studio: 是否使用 LM Studio 进行段落分类。
        save_json: 是否保存逐段分类结果，供后续人工复核。

    Returns:
        解析成功的公告列表。
    """
    with Session(engine) as session:
        statement = select(BulletinList)
        if test_date is not None:
            statement = statement.where(BulletinList.date == test_date)
        if target_name:
            statement = statement.where(BulletinList.name == target_name)

        buletin_list: Sequence[BulletinList] = session.exec(statement).all()
        res_list: list[BulletinDB] = []
        failed_names: list[str] = []
        attempted_count = 0

        for res in buletin_list:
            bulletin_type = get_bulletin_type(res.name)
            if bulletin_type in {BulletinType.CIRCULAR, BulletinType.OTHER}:
                continue

            attempted_count += 1
            content_url: Path | None = download_notice(res)
            bulletin: BulletinDB | None = resolve_notice(
                content_path=content_url,
                bulletin_info=res,
                use_lm_studio=use_lm_studio,
                save_json=save_json
            )
            if bulletin is not None:
                res_list.append(bulletin)
            else:
                failed_names.append(res.name)

        if target_name and not buletin_list:
            raise RuntimeError(f"未找到目标公告: {target_name}")

        if attempted_count > 0 and not res_list:
            failed_summary = "、".join(failed_names) if failed_names else "全部公告"
            raise RuntimeError(f"预处理没有成功解析任何公告: {failed_summary}")

        return res_list


def test_resolve_notice(
    test_date: str | None = None, use_lm_studio: bool = False, save_json: bool = False
) -> list[BulletinDB]:
    """兼容旧接口名称，内部复用公告预处理任务逻辑。"""
    return run_preprocess_task(test_date, use_lm_studio, save_json)



def bulletin_type():
    """输出当前被标记为 other 类型的公告，用于排查公告类型识别。"""
    with Session(engine) as session:
        statement = select(BulletinList).where(BulletinList.type == BulletinType.OTHER)
        buletin_list = session.exec(statement).all()
        for res in buletin_list:
            bulletin_info = DownloadBulletin(
                name=res.name, href=res.href, date=res.date
            )
            logger.info(bulletin_info)


recycle_bin_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath("recycleBin")


def resolve_file():
    """扫描本地 routine 公告文件，检查标题推断出的公告类型。"""
    root_dir_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath("routine")
    # root_dir_path = Path(recycle_bin_path).joinpath('routine')
    for root, dirs, files in os.walk(root_dir_path):
        if root != "bulletins/routine" and "source.html" in files:
            file_path = Path(root).joinpath("source.html")
            content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, "html5lib")
            title_tag = soup.title
            if isinstance(title_tag, Tag):
                current_bulletin_type = get_bulletin_type(title_tag.text)
                if current_bulletin_type in {BulletinType.ROUTINE}:
                    logger.info("%s，%s", current_bulletin_type.value, root)
                else:
                    logger.info("%s,type:%s", title_tag.text, current_bulletin_type.value)
                    # dst_path = recycle_bin_path.joinpath(type.value)
                    # logger.info(Path(root))
                    # logger.info(dst_path)
                    # shutil.move(Path(root), dst_path)
            else:
                logger.error("roots,%s, error", root)
            # logger.info("roots,%s", root)
            # logger.info("dirs,%s", dirs)
            # logger.info("files,%s", files)


def rename_file(type:str="routine"):
    """根据公告标题中的日期推断本地目录应使用的日期。

    当前函数只记录推断结果，实际重命名逻辑仍保留为注释，避免误改本地文件。

    Args:
        type: 要扫描的公告类型目录。
    """
    root_dir_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath(type)
    for root, dirs, files in os.walk(root_dir_path):
        if root != f"bulletins/{type}" and "source.html" in files:
            file_path = Path(root).joinpath("source.html")
            content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, "html5lib")
            title_tag = soup.title
            if isinstance(title_tag, Tag):
                title_name = title_tag.text
                date_pattern = re.compile(r"(\d{1,2})月(\d{1,2})日")
                dates = date_pattern.findall(title_name)
                date_pattern_root = r"\d{4}-\d{2}-\d{2}"
                match = re.search(date_pattern_root, root.__str__())
                if match is None:
                    logger.info("root %s, %s", date_pattern_root, root)
                    return
                root_date = match.group()
                date_obj = datetime.strptime(root_date, "%Y-%m-%d")
                new_date_obj = date_obj.replace(
                    month=int(dates[0][0]), day=int(dates[0][1])
                )
                new_date = new_date_obj.strftime("%Y-%m-%d")
                # if root_date != new_date:
                #     logger.info("old - %s,new - %s", root_date, new_date)
                    # new_root = Path(root).with_name(new_date)
                    # root_path = Path(root)
                    # root_path.rename(new_root)
