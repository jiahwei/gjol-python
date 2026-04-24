"""预处理任务后台 worker。"""

import asyncio
import contextlib
import logging

from sqlalchemy.exc import OperationalError

from src.dev.service import run_preprocess_task
from src.preprocess.schemas import PreprocessTask
from src.preprocess.service import (
    acquire_next_preprocess_task,
    mark_preprocess_task_done,
    mark_preprocess_task_failed,
)

logger = logging.getLogger("preprocess_worker")


class PreprocessWorker:
    """管理预处理后台 worker 的生命周期。"""

    def __init__(self) -> None:
        self.worker_task: asyncio.Task[None] | None = None
        self.stop_event: asyncio.Event | None = None

    async def start(self, poll_interval: float = 2.0) -> None:
        """启动单并发预处理 worker。"""
        if self.worker_task is not None and not self.worker_task.done():
            return

        self.stop_event = asyncio.Event()
        self.worker_task = asyncio.create_task(
            _worker_loop(self.stop_event, poll_interval),
            name="preprocess-worker",
        )
        logger.info("预处理 worker 已启动")

    async def stop(self) -> None:
        """停止 worker 循环。"""
        if self.stop_event is not None:
            self.stop_event.set()

        if self.worker_task is not None and not self.worker_task.done():
            self.worker_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.worker_task

        self.stop_event = None
        self.worker_task = None
        logger.info("预处理 worker 已停止")


preprocess_worker = PreprocessWorker()


async def start_preprocess_worker(poll_interval: float = 2.0) -> None:
    """启动单并发预处理 worker。"""
    await preprocess_worker.start(poll_interval)


async def stop_preprocess_worker() -> None:
    """停止 worker 循环。

    如果正在线程里执行大模型任务，取消协程不会立刻终止底层同步函数；
    下一步若需要强制中断，需要把模型调用本身也设计成可取消。
    """
    await preprocess_worker.stop()


async def _worker_loop(stop_event: asyncio.Event, poll_interval: float) -> None:
    while not stop_event.is_set():
        try:
            task = await asyncio.to_thread(acquire_next_preprocess_task)
        except OperationalError as exc:
            logger.warning("预处理任务表暂不可用: %s", exc)
            await asyncio.sleep(poll_interval)
            continue
        except Exception:  # pylint: disable=broad-exception-caught
            logger.exception("获取预处理任务失败")
            await asyncio.sleep(poll_interval)
            continue

        if task is None:
            await asyncio.sleep(poll_interval)
            continue

        await _run_task(task)


async def _run_task(task: PreprocessTask) -> None:
    logger.info("开始执行预处理任务: id=%s, date=%s", task.id, task.target_date)

    try:
        resolved_items = await asyncio.to_thread(
            run_preprocess_task,
            task.target_date,
            task.use_lm_studio,
            task.save_json,
        )
        await asyncio.to_thread(mark_preprocess_task_done, task.id, len(resolved_items))
        logger.info(
            "预处理任务完成: id=%s, date=%s, count=%d",
            task.id,
            task.target_date,
            len(resolved_items),
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        logger.exception("预处理任务失败: id=%s, date=%s", task.id, task.target_date)
        await asyncio.to_thread(mark_preprocess_task_failed, task.id, str(exc))
