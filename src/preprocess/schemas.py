"""预处理任务队列的接口类型。"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class PreprocessTaskStatus(str, Enum):
    """预处理任务状态。"""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class CreatePreprocessTaskPayload(BaseModel):
    """创建预处理任务的请求体。"""

    model_config = ConfigDict(populate_by_name=True)

    target_date: str = Field(alias="targetDate")
    target_name: str | None = Field(default=None, alias="targetName")
    use_lm_studio: bool = Field(default=True, alias="useLmStudio")
    save_json: bool = Field(default=True, alias="saveJson")
    model_name: str | None = Field(default=None, alias="modelName")


class PreprocessTask(BaseModel):
    """预处理任务展示模型。"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    task_type: str = Field(alias="taskType")
    target_date: str = Field(alias="targetDate")
    target_name: str | None = Field(default=None, alias="targetName")
    use_lm_studio: bool = Field(alias="useLmStudio")
    save_json: bool = Field(alias="saveJson")
    model_name: str | None = Field(default=None, alias="modelName")
    status: PreprocessTaskStatus
    created_at: str = Field(alias="createdAt")
    started_at: str | None = Field(default=None, alias="startedAt")
    finished_at: str | None = Field(default=None, alias="finishedAt")
    resolved_count: int | None = Field(default=None, alias="resolvedCount")
    error_message: str | None = Field(default=None, alias="errorMessage")
