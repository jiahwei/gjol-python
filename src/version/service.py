import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from typing import Union, List, Optional
from sqlmodel import Session, select, and_, desc,or_,delete

from src.database import get_session, engine
from src.bulletin.models import BulletinDB
from src.version.models import Version
from src.version.schemas import VersionInfo
from constants import HEADER


import logging
logger = logging.getLogger('spiders_test')

def download_reslease():
    """下载版本数据"""
    base_url = "https://gjol.wangyuan.com/info/huod/version{}.shtml"
    resList: List[Version] = []
    for i in range(3):
        url = (
            base_url.format(i)
            if i != 0
            else "https://gjol.wangyuan.com/info/huod/version.shtml"
        )
        res = requests.get(url, headers=HEADER).text
        soup = BeautifulSoup(res, "lxml")
        allList = soup.find("div", class_="group_list").find_all("li")  # type: ignore
        for li in allList:
            name = li.span.string
            time = li.p.i.string
            date = datetime.strptime(time, "%Y.%m.%d")
            res_date = date.strftime("%Y-%m-%d")
            resList.append(
                Version(
                    name=name, start_date=res_date, end_date="", acronyms="", total=0
                )
            )
    return resList


def get_version_info_by_bulletin_date(bulletin_date: str,total_leng:int) -> VersionInfo | None:
    with Session(engine) as session:
        statement = select(Version).filter(
            and_(
                Version.start_date <= bulletin_date,
                or_(
                    Version.end_date >= bulletin_date,
                    Version.end_date == None
                )
            )
        )
        result = session.exec(statement).first()
        if result is None:
            return None
        version_info = result.model_dump()
        version_id = version_info["id"]
        statement_bulletin = (
            select(BulletinDB)
            .where(BulletinDB.version_id == version_id)
            .order_by(desc(BulletinDB.total_leng))
        )
        bulletin_list_by_version_id = session.exec(statement_bulletin).all()
        logger.info('bulletin_list_by_version_id')
        logger.info(bulletin_list_by_version_id)
        if(len(bulletin_list_by_version_id) == 0):
            logger.warning('order 设置失败')
            return VersionInfo(version_id=version_id,rank = -1)
        rank = 1
        for bulletin in bulletin_list_by_version_id:
            if bulletin.total_leng < total_leng:
                break;
            rank += 1
        return VersionInfo(version_id=version_id,rank = -1)


def sort_version():
    with Session(engine) as session:
        statement = select(Version).order_by(Version.start_date)
        sorted_versions = session.exec(statement).all()


        delete_statement = select(Version)
        old_versions = session.exec(delete_statement).all()
        for version in old_versions:
            session.delete(version)

        session.commit()
        for i, version in enumerate(sorted_versions):
            new_version = Version(id= i + 1, name=version.name, start_date=version.start_date, end_date=version.end_date, acronyms=version.acronyms, fake_version=version.fake_version, total=version.total )
            session.add(new_version)

        session.commit()