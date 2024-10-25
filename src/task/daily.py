from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from fastapi import  Depends
from src.database import get_session,engine
from sqlmodel import Session,select,desc

from src.bulletin.models import Bulletin
from src.spiders.service import get_download_bulletin_list,get_list_url


scheduler = BackgroundScheduler()

def periodic_function():
    print(f'定时执行的操作时间：{datetime.now()}')
    first_date_str = get_new_date()
    for i in range(1):
        url = get_list_url(i)
        download_bulletin_list = get_download_bulletin_list(url,first_date_str)


async def apscheduler_start():
    scheduler.add_job(periodic_function, 'interval', seconds=3)
    scheduler.start()

def get_new_date() -> str | None:
    """查询数据库中最新一条公告的日期
    """    
    with Session(engine) as session:
        statement = select(Bulletin.bulletin_date).order_by(desc(Bulletin.bulletin_date)).limit(1)
        result = session.exec(statement)
        first_result = result.first()
        return first_result

periodic_function()

