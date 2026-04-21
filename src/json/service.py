"""标注模块数据库读写服务。"""

from collections import defaultdict
from pathlib import Path

from sqlmodel import Session, delete, select

from src.database import engine
from src.json.models import LlmPreprocessRecord, LlmReviewRecord
from src.json.schemas import LlmJson, LlmJsonMap, Status

LEGACY_LLM_JSON_PATH = Path(__file__).resolve().with_name("llm.json")


def _group_records(records: list[LlmJson]) -> LlmJsonMap:
    grouped: dict[str, list[LlmJson]] = defaultdict(list)
    for record in records:
        grouped[record.source_id].append(record)

    for source_id in grouped:
        grouped[source_id].sort(key=lambda item: item.paragraph_index)

    return LlmJsonMap(grouped)


def _load_legacy_llm_map() -> LlmJsonMap:
    if not LEGACY_LLM_JSON_PATH.exists():
        return LlmJsonMap({})

    raw_content = LEGACY_LLM_JSON_PATH.read_text(encoding="utf-8").strip()
    if not raw_content:
        return LlmJsonMap({})

    return LlmJsonMap.model_validate_json(raw_content)


def _review_required(record: LlmJson) -> bool:
    return (
        record.corrected_label != record.predicted_label
        or record.status != Status.UNPROCESSED
        or bool(record.review_note.strip())
    )


def _migrate_legacy_json_if_needed() -> None:
    with Session(engine) as session:
        has_preprocess_data = session.exec(select(LlmPreprocessRecord.id).limit(1)).first()
        has_review_data = session.exec(select(LlmReviewRecord.id).limit(1)).first()

        if has_preprocess_data or has_review_data:
            return

        legacy_map = _load_legacy_llm_map()
        if not legacy_map.root:
            return

        for source_id, records in legacy_map.root.items():
            for record in records:
                session.add(
                    LlmPreprocessRecord(
                        source_id=source_id,
                        bulletin_name=record.bulletin_name,
                        bulletin_date=record.bulletin_date,
                        paragraph_index=record.paragraph_index,
                        paragraph_text=record.paragraph_text,
                        predicted_label=str(record.predicted_label.value),
                    )
                )

                if _review_required(record):
                    session.add(
                        LlmReviewRecord(
                            source_id=source_id,
                            bulletin_name=record.bulletin_name,
                            bulletin_date=record.bulletin_date,
                            paragraph_index=record.paragraph_index,
                            paragraph_text=record.paragraph_text,
                            predicted_label=str(record.predicted_label.value),
                            corrected_label=str(record.corrected_label.value),
                            status=str(record.status.value),
                            review_note=record.review_note,
                        )
                    )

        session.commit()


def load_llm_json_map() -> LlmJsonMap:
    """读取机器预处理结果。"""
    _migrate_legacy_json_if_needed()
    with Session(engine) as session:
        statement = select(LlmPreprocessRecord).order_by(
            LlmPreprocessRecord.source_id,
            LlmPreprocessRecord.paragraph_index,
        )
        rows = session.exec(statement).all()

    records = [
        LlmJson(
            source_id=row.source_id,
            bulletin_name=row.bulletin_name,
            bulletin_date=row.bulletin_date,
            paragraph_index=row.paragraph_index,
            paragraph_text=row.paragraph_text,
            predicted_label=row.predicted_label,
            corrected_label=row.predicted_label,
            status=Status.UNPROCESSED,
            review_note="",
        )
        for row in rows
    ]
    return _group_records(records)


def save_llm_json_map(payload: LlmJsonMap) -> LlmJsonMap:
    """全量覆盖机器预处理结果表。"""
    with Session(engine) as session:
        _ = session.exec(delete(LlmPreprocessRecord))
        for source_id, records in payload.root.items():
            for record in records:
                session.add(
                    LlmPreprocessRecord(
                        source_id=source_id,
                        bulletin_name=record.bulletin_name,
                        bulletin_date=record.bulletin_date,
                        paragraph_index=record.paragraph_index,
                        paragraph_text=record.paragraph_text,
                        predicted_label=str(record.predicted_label.value),
                    )
                )
        session.commit()
    return load_llm_json_map()


def save_llm_json_records(records: list[LlmJson], source_id: str) -> LlmJsonMap:
    """按 source_id 覆盖机器预处理结果。"""
    with Session(engine) as session:
        _ = session.exec(
            delete(LlmPreprocessRecord).where(LlmPreprocessRecord.source_id == source_id)
        )
        for record in records:
            session.add(
                LlmPreprocessRecord(
                    source_id=source_id,
                    bulletin_name=record.bulletin_name,
                    bulletin_date=record.bulletin_date,
                    paragraph_index=record.paragraph_index,
                    paragraph_text=record.paragraph_text,
                    predicted_label=str(record.predicted_label.value),
                )
            )
        session.commit()
    return load_llm_json_map()


def load_review_map() -> LlmJsonMap:
    """读取人工复核结果。"""
    _migrate_legacy_json_if_needed()
    with Session(engine) as session:
        statement = select(LlmReviewRecord).order_by(
            LlmReviewRecord.source_id,
            LlmReviewRecord.paragraph_index,
        )
        rows = session.exec(statement).all()

    records = [
        LlmJson(
            source_id=row.source_id,
            bulletin_name=row.bulletin_name,
            bulletin_date=row.bulletin_date,
            paragraph_index=row.paragraph_index,
            paragraph_text=row.paragraph_text,
            predicted_label=row.predicted_label,
            corrected_label=row.corrected_label,
            status=row.status,
            review_note=row.review_note,
        )
        for row in rows
    ]
    return _group_records(records)


def save_review_map(payload: LlmJsonMap) -> LlmJsonMap:
    """全量覆盖人工复核结果表。"""
    with Session(engine) as session:
        _ = session.exec(delete(LlmReviewRecord))
        for source_id, records in payload.root.items():
            for record in records:
                session.add(
                    LlmReviewRecord(
                        source_id=source_id,
                        bulletin_name=record.bulletin_name,
                        bulletin_date=record.bulletin_date,
                        paragraph_index=record.paragraph_index,
                        paragraph_text=record.paragraph_text,
                        predicted_label=str(record.predicted_label.value),
                        corrected_label=str(record.corrected_label.value),
                        status=str(record.status.value),
                        review_note=record.review_note,
                    )
                )
        session.commit()
    return load_review_map()
