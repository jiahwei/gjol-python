from typing import Union, List, Optional
from pydantic import BaseModel, Field
from datetime import date



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

