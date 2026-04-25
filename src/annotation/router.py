"""标注模块接口。"""

from fastapi import APIRouter, HTTPException, Query

from src.annotation.schemas import LlmAnnotationMap
from src.annotation.service import (
    list_preprocessed_bulletin_uuids,
    load_preprocess_annotation_map,
    load_review_map,
    save_review_map,
)
from src.utils.http import success_response
from src.utils.schemas import Response

router = APIRouter()


@router.get("/preprocess", response_model=Response[LlmAnnotationMap])
def get_preprocess_annotations(
    bulletin_uuid: str | None = Query(default=None, alias="bulletinUuid"),
) -> Response[LlmAnnotationMap]:
    """读取机器预处理结果。"""
    try:
        return success_response(load_preprocess_annotation_map(bulletin_uuid))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取预处理结果失败: {exc}") from exc


@router.get("/preprocessed-bulletin-uuids", response_model=Response[list[str]])
def get_preprocessed_bulletin_uuids() -> Response[list[str]]:
    """读取已有机器预处理记录的公告 UUID 列表。"""
    try:
        return success_response(list_preprocessed_bulletin_uuids())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取已预处理公告失败: {exc}") from exc


@router.get("/review", response_model=Response[LlmAnnotationMap])
def get_review_annotations(
    bulletin_uuid: str | None = Query(default=None, alias="bulletinUuid"),
) -> Response[LlmAnnotationMap]:
    """读取人工复核结果。"""
    try:
        return success_response(load_review_map(bulletin_uuid))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"读取复核结果失败: {exc}") from exc


@router.put("/review", response_model=Response[LlmAnnotationMap])
def update_review_annotations(
    payload: LlmAnnotationMap,
    bulletin_uuid: str | None = Query(default=None, alias="bulletinUuid"),
) -> Response[LlmAnnotationMap]:
    """保存人工复核结果，传入 bulletinUuid 时只覆盖单个公告。"""
    try:
        return success_response(save_review_map(payload, bulletin_uuid))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"保存复核结果失败: {exc}") from exc
