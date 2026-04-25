"""标注模块数据库读写服务。"""

from collections import defaultdict

from sqlalchemy import null
from sqlmodel import Session, col, delete, select

from src.bulletin_list.models import BulletinList
from src.bulletin.schemas import ParagraphTopic
from src.database import engine
from src.annotation.models import LlmPreprocessRecord, LlmReviewRecord
from src.annotation.schemas import LlmAnnotation, LlmAnnotationMap, Status


def _group_records(records: list[LlmAnnotation]) -> LlmAnnotationMap:
    grouped: dict[str, list[LlmAnnotation]] = defaultdict(list)
    for record in records:
        grouped[record.source_id].append(record)

    for source_id in grouped:
        grouped[source_id].sort(key=lambda item: item.paragraph_index)

    return LlmAnnotationMap(grouped)


def _get_bulletin_uuid_by_source_id(session: Session, source_id: str) -> str | None:
    if not source_id:
        return None

    bulletin = session.exec(
        select(BulletinList).where(col(BulletinList.href) == source_id).limit(1)
    ).first()
    return bulletin.uuid if bulletin else None


def load_preprocess_annotation_map(
    bulletin_uuid: str | None = None,
) -> LlmAnnotationMap:
    """读取机器预处理结果。"""
    with Session(engine) as session:
        statement = select(LlmPreprocessRecord)
        if bulletin_uuid:
            statement = statement.where(
                col(LlmPreprocessRecord.bulletin_uuid) == bulletin_uuid
            )

        statement = statement.order_by(
            col(LlmPreprocessRecord.source_id),
            col(LlmPreprocessRecord.paragraph_index),
        )
        rows = session.exec(statement).all()

    records = [
        LlmAnnotation(
            source_id=row.source_id,
            bulletin_uuid=row.bulletin_uuid,
            bulletin_name=row.bulletin_name,
            bulletin_date=row.bulletin_date,
            paragraph_index=row.paragraph_index,
            paragraph_text=row.paragraph_text,
            predicted_label=ParagraphTopic(row.predicted_label),
            corrected_label=ParagraphTopic(row.predicted_label),
            status=Status.UNPROCESSED,
            review_note="",
        )
        for row in rows
    ]
    return _group_records(records)


def list_preprocessed_bulletin_uuids() -> list[str]:
    """读取已有机器预处理记录的公告 UUID 列表。"""
    with Session(engine) as session:
        rows = session.exec(
            select(col(LlmPreprocessRecord.bulletin_uuid))
            .where(col(LlmPreprocessRecord.bulletin_uuid) != null())
            .distinct()
        ).all()

    return sorted(uuid for uuid in rows if uuid)


def save_preprocess_annotation_records(
    records: list[LlmAnnotation],
    source_id: str,
    bulletin_uuid: str | None = None,
) -> LlmAnnotationMap:
    """按公告 UUID 覆盖机器预处理结果。"""
    with Session(engine) as session:
        resolved_bulletin_uuid = (
            bulletin_uuid or _get_bulletin_uuid_by_source_id(session, source_id)
        )

        if resolved_bulletin_uuid:
            _ = session.exec(
                delete(LlmPreprocessRecord).where(
                    col(LlmPreprocessRecord.bulletin_uuid) == resolved_bulletin_uuid
                )
            )
        else:
            _ = session.exec(
                delete(LlmPreprocessRecord).where(
                    col(LlmPreprocessRecord.source_id) == source_id
                )
            )

        for record in records:
            session.add(
                LlmPreprocessRecord(
                    source_id=source_id,
                    bulletin_uuid=record.bulletin_uuid or resolved_bulletin_uuid,
                    bulletin_name=record.bulletin_name,
                    bulletin_date=record.bulletin_date,
                    paragraph_index=record.paragraph_index,
                    paragraph_text=record.paragraph_text,
                    predicted_label=str(record.predicted_label.value),
                )
            )
        session.commit()
    return load_preprocess_annotation_map(resolved_bulletin_uuid)


def load_review_map(bulletin_uuid: str | None = None) -> LlmAnnotationMap:
    """读取人工复核结果。"""
    with Session(engine) as session:
        statement = select(LlmReviewRecord)
        if bulletin_uuid:
            statement = statement.where(
                col(LlmReviewRecord.bulletin_uuid) == bulletin_uuid
            )

        statement = statement.order_by(
            col(LlmReviewRecord.source_id),
            col(LlmReviewRecord.paragraph_index),
        )
        rows = session.exec(statement).all()

    records = [
        LlmAnnotation(
            source_id=row.source_id,
            bulletin_uuid=row.bulletin_uuid,
            bulletin_name=row.bulletin_name,
            bulletin_date=row.bulletin_date,
            paragraph_index=row.paragraph_index,
            paragraph_text=row.paragraph_text,
            predicted_label=ParagraphTopic(row.predicted_label),
            corrected_label=ParagraphTopic(row.corrected_label),
            status=Status(row.status),
            review_note=row.review_note,
        )
        for row in rows
    ]
    return _group_records(records)


def save_review_map(
    payload: LlmAnnotationMap,
    bulletin_uuid: str | None = None,
) -> LlmAnnotationMap:
    """保存人工复核结果，传入 bulletin_uuid 时只覆盖单个公告。"""
    with Session(engine) as session:
        if bulletin_uuid:
            _ = session.exec(
                delete(LlmReviewRecord).where(
                    col(LlmReviewRecord.bulletin_uuid) == bulletin_uuid
                )
            )
        else:
            _ = session.exec(delete(LlmReviewRecord))

        for source_id, records in payload.root.items():
            for record in records:
                session.add(
                    LlmReviewRecord(
                        source_id=source_id,
                        bulletin_uuid=record.bulletin_uuid
                        or bulletin_uuid
                        or _get_bulletin_uuid_by_source_id(session, source_id),
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
    return load_review_map(bulletin_uuid)
