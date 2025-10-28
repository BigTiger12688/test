"""应用统一日志配置模块，支持滚动日志与控制台输出。"""
from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

LOG_DIR = Path.home() / ".edgejsonstudio" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


def configure_logging() -> None:
    """配置日志系统，创建滚动文件和标准输出处理器。"""
    log_file = LOG_DIR / "app.log"
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.getLogger("asyncio").setLevel(logging.WARNING)
