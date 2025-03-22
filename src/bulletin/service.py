from sqlmodel import Session, select, and_, desc, or_

from src.database import get_session, engine
from src.bulletin.models import BulletinDB
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
