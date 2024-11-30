import time
from sqlmodel import Session, select, and_, desc
from src.database import get_session, engine
from src.bulletin_list.models import BulletinList

from src.spiders.service import download_notice,resolve_notice,get_bulletin_type,check_bulletin_download
from src.bulletin_list.schemas import DownloadBulletin

from pathlib import Path
import logging
loggig_path = Path('src').joinpath('spiders').joinpath("test.log")
logging.basicConfig(
    filename=loggig_path,
    filemode="a",
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


def test_resolve_notice(test_date='2023-08-30'):
    with Session(engine) as session:
        statement = select(BulletinList).where(BulletinList.date == test_date)
        buletin_list = session.exec(statement).all()
        for res in buletin_list:
            if res is not None:
                bulletin_info = DownloadBulletin(name=res.name, href=res.href, date=res.date)
                content_url = download_notice(bulletin_info)
                bulletin =  resolve_notice(content_url, bulletin_info)
                if bulletin is None:
                    logging.warning(f"get bulletin None") 
                else:
                    logging.info("get bulletin")
                    logging.info(bulletin.model_dump_json())
            else:
                logging.debug("No bulletin_info found for the given date") 


def filter_no_download_bulletin():
    with Session(engine) as session:
        statement = select(BulletinList)
        buletin_list = session.exec(statement).all()
        for res in buletin_list:
            bulletin_info = DownloadBulletin(name=res.name, href=res.href, date=res.date)
            download_notice(bulletin_info)
            # bulletin_type = get_bulletin_type(bulletin_info.name)
            # floder_name = bulletin_info.date
            # if bulletin_type is not None:
            #     is_bulletin_download = check_bulletin_download(floder_name, bulletin_type)
            #     if not is_bulletin_download:
            #         logging.info(f"{bulletin_info.name},{bulletin_info.date},未处理,{time.ctime()}")
