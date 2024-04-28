from typing import Union, List, Optional
from pydantic import BaseModel


class Content(BaseModel):
    name: str
    leng: int

class Content_Completeness(Content):
    content: str


class ArchiveDesc(BaseModel):
    """公告desc.json文件中的数据类型。

    Args:
        name (str): 公告名称
        totalLen (str): 公告文本字数
        date (str): 公告日期
        contentArr（List[Content_Completeness]）:按类型分类（PVP、PVE、PVX等）的文本信息，包含文本
        contentTotalArr[Content]）:按类型分类（PVP、PVE、PVX等）的文本信息，只记录各个类型的字数，不包含文本
        authors(str）: 作者信息
    """    
    name: str = ""
    date: str = ""
    totalLen: int = 0
    contentArr: List[Content_Completeness] = []
    contentTotalArr: List[Content] = []
    authors: str = ""
    
class PartialArchiveDesc(BaseModel):
    name: Optional[str] = None
    date: Optional[str] = None
    totalLen: Optional[int] = None
    contentArr: Optional[List[Content_Completeness]] = None
    contentTotalArr: Optional[List[Content]] = None
    authors: Optional[str] = None

class NoticeInfo(BaseModel):
    """公告列表页面下载到的公告信息

    Args:
        name (str): 公告名称
        href (str): 公告路径
        date (str): 公告日期
    """    
    name: str
    href: str
    date: str

class ReleaseInfo(BaseModel):
    """版本信息

    Args:
        name (str): 版本名称
        acronyms (str): 版本简称
        start_date (str): 开始日期
        end_date (str): 结束日期
        total (int): 总更新文本字数
    """    
    name:str
    acronyms:str
    start_date:str
    end_date:str
    total:int = 0