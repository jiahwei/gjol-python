"""段落标注 JSON 接口。"""
from fastapi import APIRouter, HTTPException

from src.json.schemas import LlmJsonMap
from src.json.service import load_llm_json_map, save_llm_json_map
from src.utils.http import success_response
from src.utils.schemas import Response

router = APIRouter()


@router.get("/llm", response_model=Response[LlmJsonMap])
def get_llm_json() -> Response[LlmJsonMap]:
    """全量读取 llm.json。"""
    try:
        return success_response(load_llm_json_map())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取 llm.json 失败: {exc}") from exc


@router.put("/llm", response_model=Response[LlmJsonMap])
def update_llm_json(payload: LlmJsonMap) -> Response[LlmJsonMap]:
    """全量覆盖 llm.json。"""
    try:
        return success_response(save_llm_json_map(payload))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存 llm.json 失败: {exc}") from exc
