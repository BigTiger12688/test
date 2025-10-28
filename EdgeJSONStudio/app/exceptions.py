"""全局异常捕获模块，将异常记录日志并展示对话框。"""
from __future__ import annotations

import logging
import traceback

from PySide6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


def _show_exception_dialog(message: str) -> None:
    """显示错误对话框。"""
    box = QMessageBox()
    box.setIcon(QMessageBox.Critical)
    box.setWindowTitle("锋芒 JSON Studio 错误")
    box.setText("发生未处理的异常，详细信息已记录到日志。")
    box.setInformativeText(message)
    box.exec()


def install_global_exception_hook() -> None:
    """安装 sys.excepthook 捕获 Qt 主线程异常。"""
    import sys

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        formatted = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        logger.error("未捕获异常:\n%s", formatted)
        _show_exception_dialog(str(exc_value))

    sys.excepthook = handle_exception
