""" 定时任务执行的脚本
该脚本定义了一个定时任务执行的函数 `periodic_function`，并使用 `BackgroundScheduler` 类创建了一个定时任务调度器 `scheduler`。
"""
from pathlib import Path

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore

from src.bulletin.models import BulletinDB
from src.bulletin.service import update_bulletin,get_new_date
from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.service import download_bulletin_list
from src.spiders.service import download_notice, resolve_notice

scheduler = BackgroundScheduler()


def periodic_function():
    """定时执行的操作"""
    print(f"定时执行的操作时间：{datetime.now()}")
    return


def dayily_fun() -> None:
    """每天定时执行的任务"""
    bulletin_list: list[DownloadBulletin] = download_bulletin_list()
    for bulletin_info in bulletin_list:
        content_url: Path | None = download_notice(bulletin_info)
        bulletin: BulletinDB | None  = resolve_notice(content_path=content_url, bulletin_info = bulletin_info)
        if bulletin:
            update_bulletin(bulletin_info=bulletin)


async def apscheduler_start() -> None:
    """启动定时任务"""
    scheduler.add_job(periodic_function, "interval", seconds=3)
    scheduler.start()

