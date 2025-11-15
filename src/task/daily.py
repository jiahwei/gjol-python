""" 定时任务执行的脚本
每周四检查是否有新的公告内容
拉到新的公告内容，更新数据库并推送到GitHub
"""
import logging
from pathlib import Path

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore

from src.bulletin.models import BulletinDB
from src.bulletin.service import update_bulletin
from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.service import download_bulletin_list
from src.spiders.service import download_notice, resolve_notice

scheduler = BackgroundScheduler()
daily_logger = logging.getLogger("daily")

def periodic_function():
    """定时执行的操作"""
    daily_logger.info("定时执行的操作时间：%s", datetime.now())
    return


def dayily_fun() -> None:
    """每周四定时执行的任务"""
    bulletin_list: list[DownloadBulletin] = download_bulletin_list()
    for bulletin_info in bulletin_list:
        content_url: Path | None = download_notice(bulletin_info)
        bulletin: BulletinDB | None  = resolve_notice(content_path=content_url, bulletin_info = bulletin_info)
        if bulletin:
            update_bulletin(bulletin_info=bulletin)


async def apscheduler_start() -> None:
    """启动定时任务"""
    scheduler.add_job(periodic_function, "interval", hours=1)
    scheduler.start()

