from sqlmodel.sql._expression_select_cls import SelectOfScalar
from sqlmodel import Session, select, desc

from src.database import engine
from src.bulletin.models import BulletinDB
from src.bulletin_list.schemas import DownloadBulletin
from src.bulletin_list.service import get_bulletin_date, get_bulletin_type
from src.version.models import Version
from src.version.schemas import VersionInfo


def fix_bulletin_ranks(version_id: int):
    with Session(engine) as session:
        statement_bulletin = (
            select(BulletinDB)
            .where(BulletinDB.version_id == version_id)
            .order_by(desc(BulletinDB.total_leng))
        )
        bulletin_list_by_version_id = session.exec(statement_bulletin).all()

        # 重新计算 rank_id
        for rank, bulletin in enumerate(bulletin_list_by_version_id, start=1):
            bulletin.rank_id = rank
            session.add(bulletin)

        session.commit()


def query_bulletin(bulletin_info: DownloadBulletin) -> BulletinDB:
    """
    查询公告信息,如果不存在则返回新创建的基础公告信息对象

    Args:
        bulletin_info (DownloadBulletin): 下载公告的基本信息

    Returns:
        BulletinDB: 数据库中已存在的公告或新创建的公告对象
    """    
    with Session(engine) as session:
        statement: SelectOfScalar[BulletinDB] = select(BulletinDB).where(
            BulletinDB.bulletin_name == bulletin_info.name
        )
        bulletin: BulletinDB | None = session.exec(statement).first()
        
        if bulletin:
            result: BulletinDB = BulletinDB.model_validate(bulletin.model_dump())
            session.close()
            return result
        else:
            session.close()
            return BulletinDB(
                bulletin_date=get_bulletin_date(bulletin_info),
                total_leng=0,
                content_total_arr="",
                bulletin_name=bulletin_info.name,
                version_id=None,
                rank_id=0,
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
            statement: SelectOfScalar[BulletinDB] = select(BulletinDB).where(
                BulletinDB.id == bulletin_info.id
            )
            bulletin: BulletinDB | None = session.exec(statement).first()
            if bulletin:
                # 更新字段
                bulletin.content_total_arr = bulletin_info.content_total_arr
                bulletin.total_leng = bulletin_info.total_leng
                session.add(bulletin)
                session.commit()
                session.refresh(bulletin)
