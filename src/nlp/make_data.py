from bs4 import BeautifulSoup, Tag
from sqlmodel import Session, select, and_, desc,update
from datetime import datetime
import pandas as pd
import logging,json,csv
import os

from src.database import get_session, engine
from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import DownloadBulletin,BulletinType
from src.bulletin_list.service import get_bulletin_date,get_bulletin_type,get_really_bulletin_date
from src.spiders.service import download_notice,resolve_notice
from src.nlp.service import predict_paragraph_category,preprocess_text


logger = logging.getLogger('nlp_test')


def make_train_csv():
    with Session(engine) as session:
        statement = select(BulletinList).where(BulletinList.type != 'circular')
        buletin_list = session.exec(statement).all()
        data = []
        for res in buletin_list[-30:-10]:
            if res is not None:
                new_date = get_really_bulletin_date(res)
                bulletin_info = DownloadBulletin(name=res.name, href=res.href, date=new_date)
                content_url = download_notice(bulletin_info)
                if content_url is None:
                    print("content_url None")
                    continue
                logger.info(f"处理{content_url}",)
                content = content_url.read_text(encoding="utf-8")
                soup = BeautifulSoup(content, "html5lib")
                details_div = soup.find("div", class_="details")
                if not isinstance(details_div, Tag):
                    return
                paragraphs = details_div.find_all("p")
                paragraph_texts = [p.get_text(strip=True) for p in paragraphs]
                for p_text in paragraph_texts:
                    words = preprocess_text(p_text)
                    if words.strip():
                        catrgory = predict_paragraph_category(words)
                        data.append({'paragraph':p_text,"label":catrgory})
        if data:
            logger.info(data)
            csv_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            df = pd.DataFrame(data)
            df[['paragraph', 'label']].to_csv(f"data/uncheck/paragraph_{csv_name}.csv", mode='a', index=False, header=True, quoting=csv.QUOTE_ALL)
        else:
             print("No bulletin_info found for the given date")
