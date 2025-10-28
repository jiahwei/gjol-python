"""公告模块数据类型

定义了数据传输对象 (DTO)，主要用于 API 接口的请求和响应
"""

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field

from src.bulletin_list.schemas import BulletinType


class DatePayload(BaseModel):
    """接口“bulletins/byDate”的入参类型

    Args:
        BaseModel (_type_): _description_
    """
    start_date: date | None = Field(None, alias="startDate")
    end_date: date | None = Field(None, alias="endDate")


class BaseBulletinInfo(BaseModel):
    """公告基本信息

    Args:
        BaseModel (_type_): _description_
    """
    date: str = ""
    orderId: int = 0
    totalLen: int = 0


class ParagraphTopic(Enum):
    """公告段落的分类标准

    Args:
        Enum (_type_): _description_
    """
    FORMAT = "format"
    UNUPDATE = "noUpdate"
    STORE = "mall"
    SKILL = "classAdjust"
    SYSTEM = "generalAdjust"
    PVP = "PVP"
    PVE = "PVE"
    PVX = "PVX"
    # FORMAT = "格式"
    # UNUPDATE = "无更新"
    # STORE = "商城"
    # SKILL = "职业调整"
    # SYSTEM = "通用调整"
    # PVP = "PVP"
    # PVE = "PVE"
    # PVX = "PVX"

CHINESE_LABELS = {
    ParagraphTopic.FORMAT: "格式",
    ParagraphTopic.UNUPDATE: "无更新",
    ParagraphTopic.STORE: "商城",
    ParagraphTopic.SKILL: "职业调整",
    ParagraphTopic.SYSTEM: "通用调整",
    ParagraphTopic.PVP: "PVP",
    ParagraphTopic.PVE: "PVE",
    ParagraphTopic.PVX: "PVX",
}

class ContentTotal(BaseModel):
    """接口“bulletins/byDate”的返回参数中content_total_arr的类型

    Args:
        BaseModel (_type_): _description_
    """
    type: ParagraphTopic
    leng: int
    content: list[str]

    class Config:
        """配置类，用于设置 Pydantic 模型的行为，这里使用枚举的 实际值 而不是枚举的 名称

        Args:
            BaseModel (_type_): _description_
        """
        use_enum_values: bool = True


class BulletinInfo(BaseBulletinInfo):
    """接口“bulletins/byDate”的返回参数

    Args:
        BaseBulletinInfo (_type_): _description_
    """
    id: int | None
    name: str | None
    order: int
    order_by_date: int
    content_total_arr: list[ContentTotal] | None = Field(None, alias="contentTotalArr")
    version_id: int | None = Field(None, alias="versionId")
    version_name: str | None = Field(None, alias="versionName")
    type: str = Field(default=BulletinType.ROUTINE)

class BulletinInVersion(BaseBulletinInfo):
    """接口“bulletins/listInVersion”的返回参数中公告的类型

    Args:
        BaseBulletinInfo (_type_): _description_
    """
    type: str


class ListInVersionReturn(BaseModel):
    """接口“bulletins/listInVersion”的返回参数

    Args:
        id (int | None): 版本ID
        acronyms (str): 版本名称
        date (str): 版本日期
        total_version_len (int, optional): 版本总长度. Defaults to 0.
        list (list[BaseBulletinInfo], optional): 公告列表. Defaults to [].
    """

    id: int | None
    acronyms: str
    start: str
    end: str
    total_version_len: int = Field(0, alias="totalVersionLen")
    list: list[BulletinInVersion]


# class bulletinAllInfo(BaseModel):
#     id: int
#     total_len: int
#     name: str
#     authors: str
#     version_id: int
#     order: int

#     class Config:
#         from_attributes: bool = True
