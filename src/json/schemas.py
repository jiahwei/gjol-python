"""json模块数据类型

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



class LlmJson(BaseModel):
    """deepseek-r1:14b解析后的公告数据
    """
    source_id: str = ""
    bulletin_name: str | None = None
    bulletin_date: str
    paragraph_index: int = 0
    paragraph_text: str = ""
    predicted_label: ParagraphTopic
    corrected_label: ParagraphTopic
    status: Status = Status.UNPROCESSED
    review_note: str = ""


class LlmJsonList(BaseModel):
    """deepseek-r1:14b解析后的公告数据列表
    """
    llm_json_list: list[LlmJson] = Field(default_factory=list)


class LlmJsonMap(RootModel[dict[str, list[LlmJson]]]):
    """deepseek-r1:14b解析后的公告数据映射
    """
