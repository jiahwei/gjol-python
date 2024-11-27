import requests
from bs4 import BeautifulSoup
from datetime import date, datetime, timedelta
from typing import Union, List, Optional
from sqlmodel import Session, select, and_, desc,or_

from src.database import get_session, engine
from src.bulletin.models import Bulletin
from src.version.models import Version
from src.version.schemas import VersionInfo
from constants import HEADER


import logging
from pathlib import Path
loggig_path = Path("src").joinpath("spiders").joinpath("test.log")
logging.basicConfig(
    filename=loggig_path,
    filemode="a",
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
)

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
            select(Bulletin)
            .where(Bulletin.version_id == version_id)
            .order_by(desc(Bulletin.total_leng))
        )
        bulletin_list_by_version_id = session.exec(statement_bulletin).all()
        logging.info('bulletin_list_by_version_id')
        logging.info(bulletin_list_by_version_id)
        if(len(bulletin_list_by_version_id) == 0):
            logging.warning('order 设置失败')
            return VersionInfo(version_id=version_id,rank = -1)
        rank = 1
        for bulletin in bulletin_list_by_version_id:
            if bulletin.total_leng < total_leng:
                break;
            rank += 1
        return VersionInfo(version_id=version_id,rank = -1)

