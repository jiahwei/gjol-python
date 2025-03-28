""" 定时任务执行的脚本
该脚本定义了一个定时任务执行的函数 `periodic_function`，并使用 `BackgroundScheduler` 类创建了一个定时任务调度器 `scheduler`。
"""
from pathlib import Path

from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from sqlmodel import Session, desc, select

from src.bulletin.models import BulletinDB
from src.bulletin.service import update_bulletin
from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.service import download_bulletin_list
from src.database import engine
from src.spiders.service import download_notice, resolve_notice

scheduler = BackgroundScheduler()


def periodic_function():
    """定时执行的操作"""
    print(f"定时执行的操作时间：{datetime.now()}")
    return


def dayily_fun() -> None:
    """每天定时执行的任务"""
    first_date_str: str | None = get_new_date()
    bulletin_list: list[DownloadBulletin] = download_bulletin_list(first_date_str)
    for bulletin_info in bulletin_list:
        content_url: Path | None = download_notice(bulletin_info)
        bulletin: BulletinDB | None  = resolve_notice(content_path=content_url, bulletin_info = bulletin_info)
        if bulletin:
            update_bulletin(bulletin_info=bulletin)


async def apscheduler_start() -> None:
    """启动定时任务"""
    scheduler.add_job(periodic_function, "interval", seconds=3)
    scheduler.start()

def get_new_date() -> str | None:
    """查询数据库中最新一条公告的日期"""
    with Session(engine) as session:
        statement = (
            select(BulletinDB.bulletin_date)
            .order_by(desc(BulletinDB.bulletin_date))
            .limit(1)
        )
        result = session.exec(statement)
        first_result = result.first()
        return first_result
