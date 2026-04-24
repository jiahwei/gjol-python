"""预处理任务接口。"""

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from src.preprocess.schemas import (
    CreatePreprocessTaskPayload,
    PreprocessTask,
    PreprocessTaskStatus,
)
from src.preprocess.service import (
    DuplicateActiveTaskError,
    InvalidTaskStateError,
    PreprocessTaskNotFoundError,
    create_preprocess_task,
    get_preprocess_task,
    list_preprocess_tasks,
    retry_preprocess_task,
)
from src.utils.http import get_current_device, success_response
from src.utils.schemas import Response

env = os.getenv("ENV", "development")

router = APIRouter(
    dependencies=[] if env == "development" else [Depends(get_current_device)],
)


@router.post("/tasks", response_model=Response[PreprocessTask])
def create_preprocess_task_route(
    payload: CreatePreprocessTaskPayload,
) -> Response[PreprocessTask]:
    """创建预处理任务，只登记任务，不在请求内执行大模型。"""
    try:
        return success_response(create_preprocess_task(payload))
    except DuplicateActiveTaskError as e:
        raise HTTPException(
            status_code=409,
            detail={"message": "该日期已经存在排队中或执行中的任务", "targetDate": str(e)},
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "创建任务失败", "error": str(e)}) from e


@router.get("/tasks", response_model=Response[list[PreprocessTask]])
def list_preprocess_task_route(
    status: PreprocessTaskStatus | None = None,
    target_date: Annotated[str | None, Query(alias="targetDate")] = None,
    limit: int = 100,
) -> Response[list[PreprocessTask]]:
    """查询预处理任务列表。"""
    try:
        safe_limit = max(1, min(limit, 500))
        return success_response(list_preprocess_tasks(status, target_date, safe_limit))
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "查询任务失败", "error": str(e)}) from e


@router.get("/tasks/{task_id}", response_model=Response[PreprocessTask])
def get_preprocess_task_route(task_id: str) -> Response[PreprocessTask]:
    """查询单个预处理任务。"""
    try:
        return success_response(get_preprocess_task(task_id))
    except PreprocessTaskNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": "任务不存在", "taskId": str(e)}) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "查询任务失败", "error": str(e)}) from e


@router.post("/tasks/{task_id}/retry", response_model=Response[PreprocessTask])
def retry_preprocess_task_route(task_id: str) -> Response[PreprocessTask]:
    """将失败任务重新放回队列。"""
    try:
        return success_response(retry_preprocess_task(task_id))
    except PreprocessTaskNotFoundError as e:
        raise HTTPException(status_code=404, detail={"message": "任务不存在", "taskId": str(e)}) from e
    except InvalidTaskStateError as e:
        raise HTTPException(status_code=409, detail={"message": "只有失败任务可以重试", "taskId": str(e)}) from e
    except DuplicateActiveTaskError as e:
        raise HTTPException(
            status_code=409,
            detail={"message": "该日期已经存在排队中或执行中的任务", "targetDate": str(e)},
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail={"message": "重试任务失败", "error": str(e)}) from e
