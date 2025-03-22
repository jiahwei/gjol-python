from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from fastapi import  Depends
from src.database import get_session,engine
from sqlmodel import Session,select,desc

from src.bulletin.models import BulletinDB
from src.bulletin_list.service import download_bulletin_list
from src.spiders.service import download_notice,resolve_notice
from src.bulletin_list.schemas import DownloadBulletin



scheduler = BackgroundScheduler()

def periodic_function():
    print(f'定时执行的操作时间：{datetime.now()}')
    return

def dayily_fun():
    first_date_str = get_new_date()
    bulletin_list = download_bulletin_list(first_date_str)
    for bulletin_info in bulletin_list:
        content_url =  download_notice(bulletin_info)
        resolve_notice(content_url,bulletin_info)


async def apscheduler_start():
    scheduler.add_job(periodic_function, 'interval', seconds=3)
    scheduler.start()

def get_new_date() -> str | None:
    """查询数据库中最新一条公告的日期
    """    
    with Session(engine) as session:
        statement = select(BulletinDB.bulletin_date).order_by(desc(BulletinDB.bulletin_date)).limit(1)
        result = session.exec(statement)
        first_result = result.first()
        return first_result