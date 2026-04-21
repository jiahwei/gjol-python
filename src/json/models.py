"""标注模块数据库模型。"""

from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class LlmPreprocessRecord(SQLModel, table=True):
    """机器预处理结果表。"""

    __tablename__ = "llm_preprocess_record"
    __table_args__ = (UniqueConstraint("source_id", "paragraph_index"),)

    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(index=True)
    bulletin_name: str | None = None
    bulletin_date: str = Field(index=True)
    paragraph_index: int = Field(index=True)
    paragraph_text: str = ""
    predicted_label: str
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class LlmReviewRecord(SQLModel, table=True):
    """人工复核结果表。"""

    __tablename__ = "llm_review_record"
    __table_args__ = (UniqueConstraint("source_id", "paragraph_index"),)

    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(index=True)
    bulletin_name: str | None = None
    bulletin_date: str = Field(index=True)
    paragraph_index: int = Field(index=True)
    paragraph_text: str = ""
    predicted_label: str
    corrected_label: str
    status: str
    review_note: str = ""
    reviewed_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
