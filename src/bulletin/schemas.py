from typing import Union, List, Optional
from pydantic import BaseModel, Field
from datetime import date
from src.bulletin_list.schemas import BulletinType
from enum import Enum


class ParagraphTopic(Enum):
    START = "开头"
    END = "署名/结尾"
    UNUPDATE = "无更新"
    STORE = "商城/外观"
    NOMAL = "通用调整"
    SKILL = "职业调整"
    PVP = "斗法调整"
    RAID = "秘境调整"
    EVENT = "活动更新" 


class DatePayload(BaseModel):
    start_date: Optional[date] = Field(None,alias="startDate")
    end_date: Optional[date] = Field(None,alias="endDate")


class BaseBulletinInfo(BaseModel):
    date: str = ""
    orderId:int = 0
    totalLen:int = 0

class ContentTotal(BaseModel):
    name:str
    leng:int
class BulletinInfo(BaseBulletinInfo):
    id:int | None
    name:str | None
    order:int
    content_total_arr:Optional[List[ContentTotal]]= Field(None,alias="contentTotalArr")
    version_id:Optional[int| None] = Field(None,alias="versionId")
    version_name:Optional[str] = Field(None,alias="versionName")
    type: str = Field(default=BulletinType.ROUTINE)

class ListInVersionReturn(BaseModel):
    id: int | None
    acronyms: str
    list: List[BaseBulletinInfo]

class bulletinAllInfo(BaseModel):
    id:int
    total_len:int
    name:str
    authors:str
    version_id:int
    order:int
    class Config:
        from_attributes = True

