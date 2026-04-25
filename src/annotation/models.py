"""标注模块数据库模型。"""

from datetime import UTC, datetime, timedelta, timezone
from typing import Any, ClassVar

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel

BEIJING_TIMEZONE = timezone(timedelta(hours=8))


def now_beijing_naive() -> datetime:
    """返回北京时间的 naive datetime，便于 SQLite 可读展示。"""
    return datetime.now(UTC).astimezone(BEIJING_TIMEZONE).replace(tzinfo=None)


class LlmPreprocessRecord(SQLModel, table=True):
    """机器预处理结果表。"""

    __tablename__: ClassVar[str] = "llm_preprocess_record"  # pyright: ignore[reportIncompatibleVariableOverride]
    __table_args__: ClassVar[tuple[Any, ...]] = (
        UniqueConstraint("source_id", "paragraph_index"),
    )

    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(index=True)
    bulletin_uuid: str | None = Field(default=None, index=True)
    bulletin_name: str | None = None
    bulletin_date: str = Field(index=True)
    paragraph_index: int = Field(index=True)
    paragraph_text: str = ""
    predicted_label: str
    created_at: datetime = Field(default_factory=now_beijing_naive, nullable=False)


class LlmReviewRecord(SQLModel, table=True):
    """人工复核结果表。"""

    __tablename__: ClassVar[str] = "llm_review_record"  # pyright: ignore[reportIncompatibleVariableOverride]
    __table_args__: ClassVar[tuple[Any, ...]] = (
        UniqueConstraint("source_id", "paragraph_index"),
    )

    id: int | None = Field(default=None, primary_key=True)
    source_id: str = Field(index=True)
    bulletin_uuid: str | None = Field(default=None, index=True)
    bulletin_name: str | None = None
    bulletin_date: str = Field(index=True)
    paragraph_index: int = Field(index=True)
    paragraph_text: str = ""
    predicted_label: str
    corrected_label: str
    status: str
    review_note: str = ""
    reviewed_at: datetime = Field(default_factory=now_beijing_naive, nullable=False)
