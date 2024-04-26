from typing import Union, List, Optional
from pydantic import BaseModel


class Content(BaseModel):
    name: str
    leng: int

class Content_Completeness(Content):
    content: str


class ArchiveDesc(BaseModel):
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
    name: str
    href: str
    date: str
