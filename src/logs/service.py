import logging
import logging.config
from pathlib import Path

from src.task import daily

# 定义日志文件路径
common_log_path = Path("src/logs/common.log")
nlp_test_path = Path("src/logs/nlp_test.log")
spiders_test_path = Path("src/logs/spiders_test.log")
spiders_history_path = Path("src/logs/spiders_history.log")
daily_path = Path("src/logs/daily.log")
# 如果需要更多模块，继续添加路径

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,  # 保留已存在的日志器
    "formatters": {
        "verbose": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "simple": {
            "format": "%(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "common_handler": {
            "class": "logging.FileHandler",
            "level": "WARNING",
            "formatter": "verbose",
            "filename": str(common_log_path),
            "encoding": "utf-8",
            "mode":"a",
        },
        "nlp_test_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": str(nlp_test_path),
            "encoding": "utf-8",
            "mode":"a",
        },
        "spiders_test_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": str(spiders_test_path),
            "encoding": "utf-8",
            "mode":"a",
        },
        "spiders_history_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": str(spiders_history_path),
            "encoding": "utf-8",
            "mode":"a",
        },
        "daily_handler": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": str(daily_path),
            "encoding": "utf-8",
            "mode":"a",
        },
        # 可以为更多模块添加处理器
    },
    "loggers": {
        "nlp_test": {
            "handlers": ["nlp_test_handler"],
            "level": "DEBUG",
            "propagate": False,  # 防止日志向上传播
        },
        "spiders_test": {
            "handlers": ["spiders_test_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "spiders_history": {
            "handlers": ["spiders_history_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        "daily": {
            "handlers": ["daily_handler"],
            "level": "DEBUG",
            "propagate": False,
        },
        # 为更多模块添加日志器
    },
    "root": {
        "handlers": ["common_handler"],
        "level": "WARNING",
    },
}
