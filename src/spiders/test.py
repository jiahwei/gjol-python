import time,os,shutil
from sqlmodel import Session, select, and_, desc,update
from src.database import get_session, engine
from pathlib import Path
from bs4 import BeautifulSoup, Tag

from constants import DEFAULT_FLODER_PATH_ABSOLUTE,BASEURL,DEFAULT_FLODER_PATH
from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import DownloadBulletin,BulletinType
from src.bulletin_list.service import get_bulletin_date,get_bulletin_type
from src.spiders.service import download_notice,resolve_notice

from pathlib import Path
import logging
loggig_path = Path("src").joinpath("spiders").joinpath("test.log")
logging.basicConfig(
    filename=loggig_path,
    filemode="w",
    level=logging.DEBUG,
    format="%(name)s - %(levelname)s - %(message)s",
    encoding="utf-8"
)


def test_resolve_notice(test_dade = None):
    with Session(engine) as session:
        statement = select(BulletinList) if test_dade is None else select(BulletinList) .where(BulletinList.date == test_dade)
        buletin_list = session.exec(statement).all()
        for res in buletin_list:
            if res is not None:
                bulletin_info = DownloadBulletin(name=res.name, href=res.href, date=res.date)
                content_url = download_notice(bulletin_info)
                bulletin =  resolve_notice(content_url, bulletin_info)
                if bulletin is None:
                    logging.warning(f"get bulletin None:{bulletin_info.name}") 
                else:
                    logging.info(f"get bulletin:{bulletin_info.name},{bulletin_info.date}")
                    logging.info(bulletin.model_dump_json())
            else:
                logging.debug("No bulletin_info found for the given date") 


def bulletin_type():
    with Session(engine) as session:
        statement = select(BulletinList).where(BulletinList.type == BulletinType.OTHER)
        buletin_list = session.exec(statement).all()
        for res in buletin_list:
            bulletin_info = DownloadBulletin(name=res.name, href=res.href, date=res.date)
            logging.info(bulletin_info)


recycle_bin_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath('recycleBin')
def resolve_file():
    root_dir_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath('version')
    for root, dirs, files in os.walk(root_dir_path):
        if root != "bulletins/version" and  'source.html' in files:
            file_path = Path(root).joinpath('source.html')
            content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, "html5lib")
            title_tag  = soup.title
            if isinstance(title_tag, Tag):
                type = get_bulletin_type(title_tag.text)
                if type in {BulletinType.VERSION} :
                    logging.info(f'VERSION{title_tag.text}')
                else:
                    logging.info(f'{title_tag.text},type:{type.value}')
                    dst_path = recycle_bin_path.joinpath(type.value)
                    # logging.info(Path(root))
                    # logging.info(dst_path)
                    # shutil.move(Path(root), dst_path)
            else:
                logging.error(f"roots,{root}, error")
            # logging.info(f"roots,{root}")
            # logging.info(f"dirs,{dirs}")
            # logging.info(f"files,{files}")
