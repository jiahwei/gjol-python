from sqlmodel import Session, select, and_, desc
from src.database import get_session, engine
from src.bulletin_list.models import BulletinList

from src.spiders.service import download_notice,resolve_notice
from src.bulletin_list.schemas import DownloadBulletin

from pathlib import Path
import logging
loggig_path = Path('src').joinpath('spiders').joinpath("test.log")
logging.basicConfig(
    filename=loggig_path,
    filemode="a",
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
)


def test_resolve_notice(test_date='2019-10-16'):
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
