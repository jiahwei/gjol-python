"""标注模块数据类型

"""
from enum import Enum

from pydantic import BaseModel, Field, RootModel

from src.bulletin.schemas import ParagraphTopic

class Status(Enum):
    """状态枚举
    """
    UNPROCESSED = "未处理"
    CONFIRMED = "已确认"
    CORED = "已修正"



class LlmAnnotation(BaseModel):
    """大模型解析后的公告段落标注数据。"""
    source_id: str = ""
    bulletin_uuid: str | None = None
    bulletin_name: str | None = None
    bulletin_date: str
    paragraph_index: int = 0
    paragraph_text: str = ""
    predicted_label: ParagraphTopic
    corrected_label: ParagraphTopic
    status: Status = Status.UNPROCESSED
    review_note: str = ""


class LlmAnnotationList(BaseModel):
    """大模型解析后的公告段落标注数据列表。"""

    annotations: list[LlmAnnotation] = Field(default_factory=list)


class LlmAnnotationMap(RootModel[dict[str, list[LlmAnnotation]]]):
    """按 source_id 分组的大模型公告段落标注数据。"""
