from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

from src.bulletin_list.schemas import BulletinType


class DatePayload(BaseModel):
    start_date: date | None = Field(None,alias="startDate")
    end_date: date | None  = Field(None,alias="endDate")


class BaseBulletinInfo(BaseModel):
    date: str = ""
    orderId:int = 0
    totalLen:int = 0

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
class ContentTotal(BaseModel):
    type: ParagraphTopic
    leng: int
    content: list[str]
    
    class Config:
        use_enum_values = True  # 使用枚举值而不是枚举对象
class BulletinInfo(BaseBulletinInfo):
    id:int | None
    name:str | None
    order:int
    content_total_arr: list[ContentTotal] | None = Field(None,alias="contentTotalArr")
    version_id:int| None = Field(None,alias="versionId")
    version_name:str | None = Field(None,alias="versionName")
    type: str = Field(default=BulletinType.ROUTINE)

class ListInVersionReturn(BaseModel):
    id: int | None
    acronyms: str
    list: list[BaseBulletinInfo]

class bulletinAllInfo(BaseModel):
    id:int
    total_len:int
    name:str
    authors:str
    version_id:int
    order:int
    class Config:
        from_attributes = True

