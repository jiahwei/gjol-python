from typing import Union, List, Optional
from pydantic import BaseModel
from enum import Enum

class DownloadBulletin(BaseModel):
    """公告列表页面下载到的公告信息

    Args:
        name (str): 公告名称
        href (str): 公告路径
        date (str): 公告日期
    """    
    name: str
    href: str
    date: str


class BulletinType(Enum): 
    ROUTINE = 'routine' 
    SKILL = 'skill' 
    VERSION = 'version'
    CIRCULAR = 'circular'
    OTHER = 'other'