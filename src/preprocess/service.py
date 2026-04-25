"""SQLModel-backed 预处理任务队列仓储。"""

import os
from datetime import UTC, datetime
from uuid import uuid4

from dotenv import load_dotenv
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, SQLModel, select

from src.database import engine
from src.preprocess.models import PreprocessTaskRecord
from src.preprocess.schemas import (
    CreatePreprocessTaskPayload,
    PreprocessTask,
    PreprocessTaskStatus,
)

TASK_TYPE_PREPROCESS = "preprocess"
TRADITIONAL_MODEL_NAME = "traditional-ensemble-classifier"

_ = load_dotenv()


class DuplicateActiveTaskError(Exception):
    """同日期任务已经处于 queued/running 状态。"""


class PreprocessTaskNotFoundError(Exception):
    """任务不存在。"""


class InvalidTaskStateError(Exception):
    """任务状态不允许当前操作。"""


def ensure_preprocess_task_table() -> None:
    """创建预处理任务表和同日期活跃任务唯一索引。"""
    SQLModel.metadata.create_all(engine, tables=[PreprocessTaskRecord.__table__])
    _ensure_preprocess_task_columns()
    for index in PreprocessTaskRecord.__table__.indexes:
        index.create(bind=engine, checkfirst=True)


def _ensure_preprocess_task_columns() -> None:
    """补齐旧库缺失的预处理任务字段。"""
    column_names = {
        column["name"]
        for column in inspect(engine).get_columns(PreprocessTaskRecord.__tablename__)
    }

    if "model_name" in column_names:
        return

    with engine.begin() as connection:
        connection.execute(
            text("ALTER TABLE preprocess_tasks ADD COLUMN model_name TEXT")
        )


def _resolve_model_name(use_lm_studio: bool, model_name: str | None = None) -> str:
    """解析任务实际记录的模型名称。"""
    if model_name and model_name.strip():
        return model_name.strip()

    if not use_lm_studio:
        return TRADITIONAL_MODEL_NAME

    return os.getenv("LM_STUDIO_MODEL", "").strip() or "lm-studio"


def recover_interrupted_preprocess_tasks() -> int:
    """把服务停止时遗留的 running 任务恢复为 queued。"""
    with Session(engine) as session:
        records = session.exec(
            select(PreprocessTaskRecord).where(
                PreprocessTaskRecord.task_type == TASK_TYPE_PREPROCESS,
                PreprocessTaskRecord.status == PreprocessTaskStatus.RUNNING.value,
            )
        ).all()

        for record in records:
            record.status = PreprocessTaskStatus.QUEUED.value
            record.finished_at = None
            record.resolved_count = None
            record.error_message = "服务重启后自动恢复，等待重新执行"
            session.add(record)

        session.commit()
        return len(records)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _record_to_task(record: PreprocessTaskRecord) -> PreprocessTask:
    return PreprocessTask.model_validate(
        {
            "id": record.id,
            "task_type": record.task_type,
            "target_date": record.target_date,
            "target_name": record.target_name,
            "use_lm_studio": record.use_lm_studio,
            "save_json": record.save_json,
            "model_name": record.model_name,
            "status": record.status,
            "created_at": record.created_at,
            "started_at": record.started_at,
            "finished_at": record.finished_at,
            "resolved_count": record.resolved_count,
            "error_message": record.error_message,
        }
    )


def _get_task_record_in_session(
    session: Session,
    task_id: str,
) -> PreprocessTaskRecord | None:
    return session.get(PreprocessTaskRecord, task_id)


def create_preprocess_task(payload: CreatePreprocessTaskPayload) -> PreprocessTask:
    """创建一个 queued 状态的预处理任务。"""
    record = PreprocessTaskRecord(
        id=str(uuid4()),
        task_type=TASK_TYPE_PREPROCESS,
        target_date=payload.target_date,
        target_name=payload.target_name,
        use_lm_studio=payload.use_lm_studio,
        save_json=payload.save_json,
        model_name=_resolve_model_name(payload.use_lm_studio, payload.model_name),
        status=PreprocessTaskStatus.QUEUED.value,
        created_at=_now_iso(),
    )

    with Session(engine) as session:
        try:
            session.add(record)
            session.commit()
            session.refresh(record)
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateActiveTaskError(payload.target_date) from exc

        return _record_to_task(record)


def list_preprocess_tasks(
    status: PreprocessTaskStatus | None = None,
    target_date: str | None = None,
    limit: int = 100,
) -> list[PreprocessTask]:
    """按条件查询预处理任务列表。"""
    statement = select(PreprocessTaskRecord)

    if status is not None:
        statement = statement.where(PreprocessTaskRecord.status == status.value)

    if target_date:
        statement = statement.where(PreprocessTaskRecord.target_date == target_date)

    statement = statement.order_by(PreprocessTaskRecord.created_at.desc()).limit(limit)

    with Session(engine) as session:
        records = session.exec(statement).all()

    return [_record_to_task(record) for record in records]


def get_preprocess_task(task_id: str) -> PreprocessTask:
    """根据任务 ID 查询单个预处理任务。"""
    with Session(engine) as session:
        record = _get_task_record_in_session(session, task_id)

    if record is None:
        raise PreprocessTaskNotFoundError(task_id)

    return _record_to_task(record)


def retry_preprocess_task(task_id: str) -> PreprocessTask:
    """将 failed 状态的任务重新置为 queued。"""
    with Session(engine) as session:
        record = _get_task_record_in_session(session, task_id)
        if record is None:
            raise PreprocessTaskNotFoundError(task_id)

        if record.status != PreprocessTaskStatus.FAILED.value:
            raise InvalidTaskStateError(task_id)

        try:
            record.status = PreprocessTaskStatus.QUEUED.value
            record.started_at = None
            record.finished_at = None
            record.resolved_count = None
            record.error_message = None
            record.model_name = _resolve_model_name(
                record.use_lm_studio,
                record.model_name,
            )
            session.add(record)
            session.commit()
            session.refresh(record)
        except IntegrityError as exc:
            session.rollback()
            raise DuplicateActiveTaskError(record.target_date) from exc

        return _record_to_task(record)


def delete_preprocess_task(task_id: str) -> PreprocessTask:
    """删除一个非运行中的预处理任务。"""
    with Session(engine) as session:
        record = _get_task_record_in_session(session, task_id)
        if record is None:
            raise PreprocessTaskNotFoundError(task_id)

        if record.status == PreprocessTaskStatus.RUNNING.value:
            raise InvalidTaskStateError(task_id)

        task = _record_to_task(record)
        session.delete(record)
        session.commit()

        return task


def acquire_next_preprocess_task() -> PreprocessTask | None:
    """取出最早的 queued 任务并标记为 running。"""
    with Session(engine) as session:
        record = session.exec(
            select(PreprocessTaskRecord)
            .where(
                PreprocessTaskRecord.task_type == TASK_TYPE_PREPROCESS,
                PreprocessTaskRecord.status == PreprocessTaskStatus.QUEUED.value,
            )
            .order_by(PreprocessTaskRecord.created_at.asc())
            .limit(1)
        ).first()

        if record is None:
            return None

        record.status = PreprocessTaskStatus.RUNNING.value
        record.started_at = _now_iso()
        record.finished_at = None
        record.resolved_count = None
        record.error_message = None
        if not record.model_name:
            record.model_name = _resolve_model_name(record.use_lm_studio)
        session.add(record)
        session.commit()
        session.refresh(record)

        return _record_to_task(record)


def mark_preprocess_task_done(task_id: str, resolved_count: int) -> PreprocessTask:
    with Session(engine) as session:
        record = _get_task_record_in_session(session, task_id)
        if record is None:
            raise PreprocessTaskNotFoundError(task_id)

        record.status = PreprocessTaskStatus.DONE.value
        record.finished_at = _now_iso()
        record.resolved_count = resolved_count
        record.error_message = None
        session.add(record)
        session.commit()
        session.refresh(record)

        return _record_to_task(record)


def mark_preprocess_task_failed(task_id: str, error_message: str) -> PreprocessTask:
    with Session(engine) as session:
        record = _get_task_record_in_session(session, task_id)
        if record is None:
            raise PreprocessTaskNotFoundError(task_id)

        record.status = PreprocessTaskStatus.FAILED.value
        record.finished_at = _now_iso()
        record.error_message = error_message[:4000]
        session.add(record)
        session.commit()
        session.refresh(record)

        return _record_to_task(record)
