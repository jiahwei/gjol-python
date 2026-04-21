"""标注模块接口。"""

from fastapi import APIRouter, HTTPException

from src.json.schemas import LlmJsonMap
from src.json.service import (
    load_llm_json_map,
    load_review_map,
    save_llm_json_map,
    save_review_map,
)
from src.utils.http import success_response
from src.utils.schemas import Response

router = APIRouter()


@router.get("/llm", response_model=Response[LlmJsonMap])
def get_llm_json() -> Response[LlmJsonMap]:
    """读取机器预处理结果。"""
    try:
        return success_response(load_llm_json_map())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取预处理结果失败: {exc}") from exc


@router.put("/llm", response_model=Response[LlmJsonMap])
def update_llm_json(payload: LlmJsonMap) -> Response[LlmJsonMap]:
    """全量覆盖机器预处理结果。"""
    try:
        return success_response(save_llm_json_map(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存预处理结果失败: {exc}") from exc


@router.get("/review", response_model=Response[LlmJsonMap])
def get_review_json() -> Response[LlmJsonMap]:
    """读取人工复核结果。"""
    try:
        return success_response(load_review_map())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取复核结果失败: {exc}") from exc


@router.put("/review", response_model=Response[LlmJsonMap])
def update_review_json(payload: LlmJsonMap) -> Response[LlmJsonMap]:
    """全量覆盖人工复核结果。"""
    try:
        return success_response(save_review_map(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存复核结果失败: {exc}") from exc
