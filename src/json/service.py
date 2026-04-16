"""llm.json 的读写服务。"""
import json
import logging
from pathlib import Path

from src.json.schemas import LlmJson, LlmJsonMap

logger = logging.getLogger("spiders_test")
LLM_JSON_PATH = Path(__file__).resolve().with_name("llm.json")


def load_llm_json_map() -> LlmJsonMap:
    """读取段落标注 JSON 文件。"""
    if not LLM_JSON_PATH.exists():
        return LlmJsonMap({})

    raw_content = LLM_JSON_PATH.read_text(encoding="utf-8").strip()
    if not raw_content:
        return LlmJsonMap({})

    try:
        return LlmJsonMap.model_validate_json(raw_content)
    except ValueError as exc:
        logger.warning("读取 llm.json 失败，将使用空数据: %s", exc)
        return LlmJsonMap({})


def save_llm_json_map(payload: LlmJsonMap) -> LlmJsonMap:
    """全量保存段落标注 JSON 数据。"""
    LLM_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    LLM_JSON_PATH.write_text(
        json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return payload


def save_llm_json_records(records: list[LlmJson], source_id: str) -> LlmJsonMap:
    """按 source_id 覆盖段落标注数据。"""
    llm_json_map = load_llm_json_map()
    llm_json_map.root[source_id] = records
    return save_llm_json_map(llm_json_map)
