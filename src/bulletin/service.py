"""公告信息服务模块
该模块提供了公告信息的查询和更新功能。
主要功能包括：
- 查询公告信息：根据公告名称查询数据库中的公告信息，如果不存在则返回新创建的基础公告信息对象。
"""
from sqlmodel import Session, select , desc


from src.database import engine
from src.bulletin.models import BulletinDB
from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.models import BulletinList
from src.bulletin_list.service import get_really_bulletin_date, get_bulletin_type
from src.version.service import get_version_id_by_date,get_bulletin_rank

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

def query_bulletin(bulletin_info: DownloadBulletin | BulletinList) -> BulletinDB:
    """
    查询公告信息,如果不存在则返回新创建的基础公告信息对象

    Args:
        bulletin_info (DownloadBulletin): 下载公告的基本信息

    Returns:
        BulletinDB: 数据库中已存在的公告或新创建的公告对象
    """
    with Session(engine) as session:
        statement = select(BulletinDB).where(
            BulletinDB.original_date == bulletin_info.date
        )
        bulletin: BulletinDB | None = session.exec(statement).first()
        if bulletin:
            result: BulletinDB = BulletinDB.model_validate(bulletin.model_dump())
            session.close()
            return result
        session.close()
        return BulletinDB(
            bulletin_date=get_really_bulletin_date(bulletin_info),
            original_date=bulletin_info.date,
            total_leng=0,
            content_total_arr="",
            bulletin_name=bulletin_info.name,
            version_id = get_version_id_by_date(bulletin_info.date),
            type=get_bulletin_type(bulletin_name=bulletin_info.name).value,
        )


def update_bulletin(bulletin_info: BulletinDB) -> None:
    """
    更新公告信息

    Args:
        bulletin_info (BulletinDB): 公告信息
    """
    with Session(engine) as session:
        if bulletin_info.id is None:
            session.add(bulletin_info)
            session.commit()
            session.refresh(bulletin_info)
        else:
            # 更新公告信息
            statement= select(BulletinDB).where(
                BulletinDB.id == bulletin_info.id
            )
            bulletin: BulletinDB | None = session.exec(statement).first()
            if bulletin:
                # 更新字段
                bulletin.content_total_arr = bulletin_info.content_total_arr
                bulletin.total_leng = bulletin_info.total_leng
                # rank:int = get_bulletin_rank(version_id = bulletin_info.version_id,total_leng= bulletin_info.total_leng)
                # bulletin.rank_id = rank
                session.add(bulletin)
                session.commit()
                session.refresh(bulletin)

# def update_bulletin_content(bulletin_info: BulletinDB) -> None:
