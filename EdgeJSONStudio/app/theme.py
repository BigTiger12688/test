"""主题管理模块，负责响应系统主题和自定义主题切换。"""
from __future__ import annotations

import logging
from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtGui import QGuiApplication, QPalette

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """管理浅色、深色和系统主题同步。"""

    currentThemeChanged = Signal(str)

    def __init__(self, settings) -> None:
        super().__init__()
        self._settings = settings
        self._current_theme = settings.theme
        self._settings.themeChanged.connect(self.apply_theme)

    @Property(str, notify=currentThemeChanged)
    def currentTheme(self) -> str:
        return self._current_theme

    def apply_initial_theme(self) -> None:
        """应用启动初始主题。"""
        self.apply_theme(self._settings.theme)

    def sync_system_palette(self) -> None:
        """同步系统调色板用于 QML 读取。"""
        app = QGuiApplication.instance()
        if app:
            palette = app.palette()
            logger.debug("系统调色板已同步: %s", palette)

    def apply_theme(self, theme: str) -> None:
        """根据设置应用主题。"""
        app = QGuiApplication.instance()
        if app is None:
            return
        palette = QPalette()
        if theme == "dark":
            palette.setColor(QPalette.Window, palette.color(QPalette.Window).darker(150))
            app.setPalette(palette)
            app.setStyleSheet("")
        elif theme == "light":
            palette.setColor(QPalette.Window, palette.color(QPalette.Window).lighter(150))
            app.setPalette(palette)
            app.setStyleSheet("")
        else:
            app.setPalette(QPalette())
            app.setStyleSheet("")
        self._current_theme = theme
        self.currentThemeChanged.emit(theme)
        logger.info("主题切换为 %s", theme)
