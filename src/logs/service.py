from pathlib import Path
import logging.config

# 确保日志目录存在
log_dir = Path("src/logs")
log_dir.mkdir(exist_ok=True, parents=True)

# 定义日志文件路径
common_log_path: Path = Path("src/logs/common.log")
nlp_test_path: Path = Path("src/logs/nlp_test.log")
spiders_test_path: Path = Path("src/logs/spiders_test.log")
spiders_history_path: Path = Path("src/logs/spiders_history.log")
daily_path: Path = Path("src/logs/daily.log")
train_path:Path = Path("src/logs/train.log")

# 确保所有日志文件存在
for log_file in [common_log_path, nlp_test_path, spiders_test_path,
                spiders_history_path, daily_path, train_path]:
    if not log_file.exists():
        log_file.touch()

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
        "train_handler" : {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "verbose",
            "filename": str(train_path),
            "encoding": "utf-8",
            "mode":"a",
        }
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
        "train": {
            "handlers": ["train_handler"],
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

def setup_logging():
    """初始化log配置
    """
    try:
        logging.config.dictConfig(LOGGING_CONFIG)
    except Exception as e:
        print(f"Error in Logging Configuration: {e}")
        logging.basicConfig(level=logging.DEBUG)
