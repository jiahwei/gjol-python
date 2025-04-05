"""版本相关的方法
该模块提供了一些与版本相关的方法，包括下载版本数据、根据公告日期和长度获取版本信息以及对数据库中的版本进行排序等功能。
"""

import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, and_, desc, or_, select

from constants import HEADER
from src.bulletin.models import BulletinDB
from src.database import engine
from src.version.models import Version
from src.version.schemas import VersionInfo

logger = logging.getLogger("spiders_test")


def download_reslease():
    """下载版本数据
    
    从官方网站爬取版本更新信息，包括版本名称和发布日期。
    爬取最近三页的版本数据，并将其转换为Version对象列表。
    
    Returns:
        list[Version]: 包含所有爬取到的版本信息的列表
    """
    base_url = "https://gjol.wangyuan.com/info/huod/version{}.shtml"
    res_list: list[Version] = []
    for i in range(3):
        url = (
            base_url.format(i)
            if i != 0
            else "https://gjol.wangyuan.com/info/huod/version.shtml"
        )
        res = requests.get(url, headers=HEADER, timeout=30).text
        soup = BeautifulSoup(res, "lxml")
        all_list = soup.find("div", class_="group_list").find_all("li")  # type: ignore
        for li in all_list:
            name = li.span.string
            time = li.p.i.string
            date = datetime.strptime(time, "%Y.%m.%d")
            res_date = date.strftime("%Y-%m-%d")
            res_list.append(
                Version(
                    name=name, start_date=res_date, end_date="", acronyms="", total=0
                )
            )
    return res_list


def get_version_id_by_date(bulletin_date: str) -> int:
    """根据公告日期获取对应的版本ID
    
    根据给定的公告日期查找对应的版本。
    
    Args:
        bulletin_date (str): 公告的发布日期，格式为"YYYY-MM-DD"
    
    Returns:
        int: 对应的版本ID，如果找不到对应版本则返回999
    """
    try:
        with Session(engine) as session:
            # 查找对应日期的版本
            statement = select(Version).filter(
                and_(
                    or_(Version.start_date.is_(None), Version.start_date <= bulletin_date),
                    or_(Version.end_date.is_(None), Version.end_date >= bulletin_date),
                )
            )
            result: Version | None = session.exec(statement).first()
            
            if result is None:
                logger.warning(f"未找到日期 {bulletin_date} 对应的版本")
                return 999

            version_id: int  = result.id if result.id is not None else 999
            return version_id
            
    except Exception as e:
        logger.error(f"获取版本ID时发生错误: {str(e)}")
        return 999


def get_bulletin_rank(version_id: int, total_leng: int) -> int:
    """计算公告在版本中的排名
    
    根据公告的总长度计算其在指定版本中的排名。
    排名基于公告的总长度，长度越大排名越靠前。
    
    Args:
        version_id (int): 版本ID
        total_leng (int): 公告的总长度（字符数）
    
    Returns:
        int: 公告在版本中的排名，如果版本下没有公告则返回1
    """
    try:
        with Session(engine) as session:
            # 获取该版本下所有公告并按总长度排序
            statement_bulletin = (
                select(BulletinDB)
                .where(BulletinDB.version_id == version_id)
                .order_by(desc(BulletinDB.total_leng))
            )
            bulletin_list_by_version_id = session.exec(statement_bulletin).all()
            
            # 如果没有公告，返回默认排名1
            if not bulletin_list_by_version_id:
                logger.warning(f"版本ID {version_id} 下没有公告，返回默认排名1")
                return 1
            
            # 计算当前公告的排名
            rank = 1
            for bulletin in bulletin_list_by_version_id:
                if bulletin.total_leng <= total_leng:
                    break
                rank += 1
            
            logger.debug(f"公告(长度:{total_leng})在版本ID {version_id} 中的排名为 {rank}")
            return rank
            
    except Exception as e:
        logger.error(f"计算公告排名时发生错误: {str(e)}")
        return 1


def sort_version():
    """对数据库中的版本进行排序
    
    按照版本的开始日期对所有版本进行排序，并重新分配ID。
    此函数会先删除数据库中的所有版本记录，然后按照排序后的顺序重新插入。
    新的ID从1开始递增分配，确保ID的连续性和有序性。
    
    注意：此操作会重置所有版本的ID，可能影响依赖于版本ID的其他数据。
    """
    with Session(engine) as session:
        statement = select(Version).order_by(Version.start_date)
        sorted_versions = session.exec(statement).all()

        delete_statement = select(Version)
        old_versions = session.exec(delete_statement).all()
        for version in old_versions:
            session.delete(version)

        session.commit()
        for i, version in enumerate(sorted_versions):
            new_version = Version(
                id=i + 1,
                name=version.name,
                start_date=version.start_date,
                end_date=version.end_date,
                acronyms=version.acronyms,
                fake_version=version.fake_version,
                total=version.total,
            )
            session.add(new_version)

        session.commit()


def fix_bulletin_ranks(version_id: int):
    """修复指定版本的公告排名
    
    根据公告的总长度对指定版本ID的所有公告重新进行排名。
    排名基于公告的total_leng字段，按降序排列，长度越大排名越靠前。
    
    Args:
        version_id (int): 需要修复排名的版本ID
    """
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