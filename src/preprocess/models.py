"""预处理任务数据库模型。"""

from typing import Any, ClassVar

from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel


class PreprocessTaskRecord(SQLModel, table=True):
    """预处理任务队列表。"""

    __tablename__: ClassVar[str] = "preprocess_tasks"  # pyright: ignore[reportIncompatibleVariableOverride]
    __table_args__: ClassVar[tuple[Any, ...]] = (
        Index(
            "uq_preprocess_tasks_active_date",
            "task_type",
            "target_date",
            unique=True,
            sqlite_where=text("status IN ('queued', 'running')"),
        ),
    )

    id: str = Field(primary_key=True)
    task_type: str = Field(index=True)
    target_date: str = Field(index=True)
    target_name: str | None = None
    use_lm_studio: bool = True
    save_json: bool = True
    model_name: str | None = None
    status: str = Field(index=True)
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    resolved_count: int | None = None
    error_message: str | None = None
