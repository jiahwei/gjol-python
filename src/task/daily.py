""" 定时任务执行的脚本
- 每天定时执行的任务：
    - 爬取最新的公告列表
    - 爬取公告详情
    - 解析公告详情
"""

from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from sqlmodel import Session, desc, select

from src.bulletin.models import BulletinDB
from src.bulletin_list.service import download_bulletin_list
from src.database import engine
from src.spiders.service import download_notice, resolve_notice

scheduler = BackgroundScheduler()


def periodic_function():
    """定时执行的操作"""
    print(f"定时执行的操作时间：{datetime.now()}")
    return


def dayily_fun():
    """每天定时执行的任务"""
    first_date_str = get_new_date()
    bulletin_list = download_bulletin_list(first_date_str)
    for bulletin_info in bulletin_list:
        content_url = download_notice(bulletin_info)
        resolve_notice(content_url, bulletin_info)


async def apscheduler_start():
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
