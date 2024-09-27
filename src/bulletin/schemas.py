from typing import Union, List, Optional
from pydantic import BaseModel, Field
from datetime import date



class DatePayload(BaseModel):
    start_date: Optional[date] = Field(None,alias="startDate")
    end_date: Optional[date] = Field(None,alias="endDate")
    show_all_info: bool = Field(default=False, alias="showAllInfo")


class BulletinInfo(BaseModel):
    date: str = ""
    orderId:int = 0
    totalLen:int = 0
class getBulletinListInVersionReturn(BaseModel):
    id: int 
    acronyms: str
    list: List[BulletinInfo]

class bulletinAllInfo(BaseModel):
    id:int
    total_len:int
    name:str
    authors:str
    version_id:int
    order:int
    class Config:
        from_attributes = True

