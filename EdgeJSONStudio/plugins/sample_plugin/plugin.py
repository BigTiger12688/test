"""示例插件，实现简单的日志功能。"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class Plugin:
    """示例插件。"""

    @property
    def meta(self):
        return {"name": "示例工具", "version": "1.0.0"}

    def activate(self) -> None:
        logger.info("示例插件已激活")

    def deactivate(self) -> None:
        logger.info("示例插件已停用")
