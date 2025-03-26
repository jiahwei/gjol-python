import time,os,shutil,re
import logging
from datetime import date, datetime, timedelta
from sqlmodel import Session, select, and_, desc,update
from src.database import get_session, engine
from pathlib import Path
from bs4 import BeautifulSoup, Tag

from constants import DEFAULT_FLODER_PATH_ABSOLUTE,BASEURL,DEFAULT_FLODER_PATH
from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import DownloadBulletin,BulletinType
from src.bulletin_list.service import get_bulletin_date,get_bulletin_type,get_really_bulletin_date
from src.spiders.service import download_notice,resolve_notice
from src.nlp.service import nlp_test

from pathlib import Path

logger = logging.getLogger('nlp_test')


def test_resolve_notice(test_dade = None):
    with Session(engine) as session:
        statement = select(BulletinList) if test_dade is None else select(BulletinList) .where(BulletinList.date == test_dade)
        buletin_list = session.exec(statement).all()
        for res in buletin_list[203:210]:
            if res is not None:
                new_date = get_really_bulletin_date(res)
                bulletin_info = DownloadBulletin(name=res.name, href=res.href, date=new_date)
                content_url = download_notice(bulletin_info)
                bulletin =  nlp_test(content_url, bulletin_info)
                # bulletin =  resolve_notice(content_url, bulletin_info)
                # bulletin =  resolve_notice_by_spacy(content_url, bulletin_info)
                if bulletin is None:
                    logger.warning(f"get bulletin None:{bulletin_info.name}") 
                    continue
                else:
                    logger.info(f"get bulletin:{bulletin_info.name},{bulletin_info.date}")
                    logger.info(bulletin)
            else:
                logger.debug("No bulletin_info found for the given date") 


def bulletin_type():
    with Session(engine) as session:
        statement = select(BulletinList).where(BulletinList.type == BulletinType.OTHER)
        buletin_list = session.exec(statement).all()
        for res in buletin_list:
            bulletin_info = DownloadBulletin(name=res.name, href=res.href, date=res.date)
            logger.info(bulletin_info)


recycle_bin_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath('recycleBin')
def resolve_file():
    root_dir_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath('routine')
    # root_dir_path = Path(recycle_bin_path).joinpath('routine')
    for root, dirs, files in os.walk(root_dir_path):
        if root != "bulletins/routine" and  'source.html' in files:
            file_path = Path(root).joinpath('source.html')
            content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, "html5lib")
            title_tag  = soup.title
            if isinstance(title_tag, Tag):
                type = get_bulletin_type(title_tag.text)
                if type in {BulletinType.ROUTINE} :
                    logger.info(f'{title_tag.text},{root}')
                else:
                    logger.info(f'{title_tag.text},type:{type.value}')
                    # dst_path = recycle_bin_path.joinpath(type.value)
                    # logger.info(Path(root))
                    # logger.info(dst_path)
                    # shutil.move(Path(root), dst_path)
            else:
                logger.error(f"roots,{root}, error")
            # logger.info(f"roots,{root}")
            # logger.info(f"dirs,{dirs}")
            # logger.info(f"files,{files}")


def rename_file(type='routine'):
    root_dir_path = Path(DEFAULT_FLODER_PATH_ABSOLUTE).joinpath(type)
    for root, dirs, files in os.walk(root_dir_path):
        if root != f"bulletins/{type}" and  'source.html' in files:
            file_path = Path(root).joinpath('source.html')
            content = file_path.read_text(encoding="utf-8")
            soup = BeautifulSoup(content, "html5lib")
            title_tag  = soup.title
            if isinstance(title_tag, Tag):
                title_name = title_tag.text
                date_pattern = re.compile(r'(\d{1,2})月(\d{1,2})日')
                dates = date_pattern.findall(title_name)
                date_pattern_root = r'\d{4}-\d{2}-\d{2}'
                match = re.search(date_pattern_root, root.__str__())
                if match is None:
                    logger.info(f'root{date_pattern_root},{root}')
                    return
                root_date = match.group()
                date_obj = datetime.strptime(root_date, '%Y-%m-%d')
                new_date_obj =date_obj.replace(month=int(dates[0][0]), day=int(dates[0][1]))
                new_date = new_date_obj.strftime('%Y-%m-%d')
                if root_date != new_date:
                    logger.info(f'old - {root_date},new - {new_date}')
                    # new_root = Path(root).with_name(new_date) 
                    # root_path = Path(root) 
                    # root_path.rename(new_root)
