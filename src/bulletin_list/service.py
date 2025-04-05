"""公告列表模块的方法
该模块提供了公告列表相关的方法，包括获取公告列表、下载公告列表、更新公告列表等功能。
"""
from bs4.element import NavigableString, Tag


import random
import re
import time
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from sqlmodel import Session, and_, desc, select

from src.bulletin_list.models import BulletinList
from src.bulletin_list.schemas import BulletinType, DownloadBulletin
from src.database import engine

header = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 Edg/117.0.2045.31"
}

def get_latest_bulletin_list() -> BulletinList:
    """查询数据库中最新的公告数据
    
    Returns:
        BulletinList: 数据库中日期最新的公告，如果数据库为空则返回默认公告对象
    """
    with Session(engine) as session:
        statement = select(BulletinList).order_by(desc(BulletinList.date)).limit(1)
        latest_info: BulletinList | None = session.exec(statement).first()
        
        if latest_info is not None:
            return latest_info
            
        # 数据库中没有记录时返回默认值
        return BulletinList(
            name="default", 
            href="", 
            date="1998-08-22", 
            type=BulletinType.OTHER.value
        )


def get_list_url(i: int = 0) -> str:
    """返回公告列表的URL

    Args:
        i (int): 第几页

    Returns:
        str: 公告列表的URL
    """
    url = "http://gjol.wangyuan.com/info/notice{}.shtml"
    if i != 0:
        base_url = url.format(i)
    else:
        base_url = "http://gjol.wangyuan.com/info/notice.shtml"
    return base_url


def get_bulletin_list(url: str, latest_date: str | None = None) -> list[DownloadBulletin]:
    """获取要下载的公告列表
    
    从指定URL获取公告列表，并根据最新日期过滤出需要下载的公告。
    同时会将获取到的所有公告信息保存到数据库中。

    Args:
        url (str): 公告列表的URL
        latest_date (str | None, optional): 数据库中最新一条公告的日期 解析公告日期存在就返回比最新日期更新的公告。

    Returns:
        list[DownloadBulletin]: 需要下载的公告列表
    """
    try:
        res: str = requests.get(url, headers=header, timeout=30).text
        soup: BeautifulSoup = BeautifulSoup(res, "lxml")
        target_div: Tag | NavigableString | None = soup.find("div", class_="list_box")
        
        if target_div is None or not isinstance(target_div, Tag):
            print(f"无法在页面中找到公告列表区域: {url}")
            return []
            
        all_list = target_div.find_all("li")
        res_list: list[DownloadBulletin] = []        
       
        for li in all_list:
            # 提取公告信息
            a_dom = li.a
            time_span = li.span
            
            if not a_dom or not time_span or not time_span.string:
                continue  # 跳过无效数据
                
            current_date: datetime = datetime.strptime(time_span.string, "%Y-%m-%d")
            
            # 创建公告对象
            bulletin_info = DownloadBulletin(
                name=a_dom.attrs.get("title", ""),
                href=a_dom.attrs.get("href", ""),
                date=time_span.string,
            )
            
            # 保存到数据库
            update_bulletin_list(info=bulletin_info)

            # 解析公告日期存在就返回比最新日期更新的公告
            if latest_date is not None:
                reference_date = datetime.strptime(latest_date, "%Y-%m-%d")
                if current_date > reference_date:
                    res_list.append(bulletin_info)
            else:
                res_list.append(bulletin_info)
        return res_list
        
    except requests.RequestException as e:
        print(f"请求公告列表失败: {url}, 错误: {e}")
        return []
    except Exception as e:
        print(f"处理公告列表时出错: {e}")
        return []


def download_bulletin_list(pageNum: int = 1,is_download_lastest:bool = True) -> list[DownloadBulletin]:
    """下载公告列表

    Args:
        pageNum (int, optional): 要下载的公告列表页数
        is_download_lastest (bool, optional): 是否只下载最新的公告

    Returns:
        list[DownloadBulletin]: 公告列表
    """
    bulletin_list: list[DownloadBulletin] = []
    first_date_str: str | None = get_latest_bulletin_list().date if is_download_lastest else None
    for i in range(pageNum):
        url: str = get_list_url(i)
        new_list: list[DownloadBulletin] = get_bulletin_list(url, first_date_str)
        bulletin_list.extend(new_list)
    return bulletin_list


def update_bulletin_list(info: DownloadBulletin):
    """更新公告列表数据库
    
    将公告信息保存到数据库中，如果数据已存在则跳过
    
    Args:
        info (DownloadBulletin): 要保存的公告信息
    """
    with Session(engine) as session:
        # 先检查数据是否已存在
        statement = select(BulletinList).where(
            and_(
                BulletinList.name == info.name,
                BulletinList.date == info.date
            )
        )
        existing = session.exec(statement).first()
        
        # 如果数据不存在，则插入
        if existing is None:
            bulletin_type = get_bulletin_type(info.name)
            new_bulletin = BulletinList(
                name=info.name, 
                href=info.href, 
                date=info.date, 
                type=bulletin_type.value
            )
            
            try:
                session.add(new_bulletin)
                session.commit()
                print(f"插入新数据成功: {info.name}")
            except Exception as e:
                session.rollback()
                print(f"插入数据失败: {info.name}, 错误: {str(e)}")
        else:
            # 数据已存在，不执行任何操作
            print(f"数据已存在，不执行插入: {info.name}")

def get_bulletin_date(bulletin_info: DownloadBulletin | BulletinList) -> str:
    year_month = bulletin_info.date[:-3]
    match = re.search(r"(\d+)月(\d+)日", bulletin_info.name)
    day = "01" if match is None else match.group(2)
    date = f"{year_month}-{day}"
    resolve_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y-%m-%d')
    return resolve_date


def get_bulletin_type(bulletin_name: str) -> BulletinType:
    """返回公告类型

    Args:
        bulletin_name (str): 公告名称

    Returns:
        BulletinType | None: 公告类型
    """
    if ("职业" in bulletin_name or "技能" in bulletin_name) and '《古剑奇谭网络版》' in bulletin_name:
        return BulletinType.SKILL
    if ("资料片" in bulletin_name or "版本" in bulletin_name) and '更新' in bulletin_name and '公告' in bulletin_name:
        return BulletinType.VERSION
    if "更新维护公告" in bulletin_name:
        return BulletinType.ROUTINE
    if "通告" in bulletin_name:
        return BulletinType.CIRCULAR
    return BulletinType.OTHER


def get_really_bulletin_date(bulletin_info: DownloadBulletin | BulletinList) -> str:
    """公告列表中的日期多数是周三，处理成周四。因为bulletins文件夹中使用更新日（周四）作为文件名

    Args:
        bulletin_info (DownloadBulletin | BulletinList): _description_

    Returns:
        str: 处理后的日期
    """
    # 混沌初开，没什么规律，直接跳过
    filter_list = ['2018-07-07','2018-07-10']
    if bulletin_info.date in filter_list:
        return bulletin_info.date
    
    date_obj = datetime.strptime(bulletin_info.date, '%Y-%m-%d')
    week_day = date_obj.weekday()

    # 如果日期是周一至周三，调整到当周的周四
    if week_day in {0, 1, 2}:  # 周一到周三
        days_to_add = 3 - week_day
        date_obj += timedelta(days=days_to_add)
    elif week_day in {4, 5, 6}:  # 周五到周日
        days_to_add = 10 - week_day  # 调整到下周四
        date_obj += timedelta(days=days_to_add)

    # 返回处理后的日期
    return date_obj.strftime('%Y-%m-%d')
