"""应用配置模块，提供可移植设置存取。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from PySide6.QtCore import QObject, Property, Signal


class AppSettings(QObject):
    """Qt 可绑定的应用设置对象。"""

    themeChanged = Signal(str)
    languageChanged = Signal(str)
    networkEnabledChanged = Signal(bool)

    def __init__(self, portable: bool = False) -> None:
        super().__init__()
        self._portable = portable
        base_dir = Path(__file__).resolve().parent.parent
        if portable:
            self._settings_dir = base_dir / "config"
        else:
            self._settings_dir = Path.home() / ".edgejsonstudio"
        self._settings_dir.mkdir(parents=True, exist_ok=True)
        self._settings_file = self._settings_dir / "settings.json"
        self._data: Dict[str, Any] = {
            "theme": "system",
            "language": "auto",
            "networkEnabled": False,
            "recentFiles": [],
        }

    def load(self) -> None:
        """加载配置文件，如不存在则写入默认值。"""
        if self._settings_file.exists():
            with self._settings_file.open("r", encoding="utf-8") as fh:
                self._data.update(json.load(fh))
        else:
            self.save()

    def save(self) -> None:
        """保存配置至磁盘。"""
        with self._settings_file.open("w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)

    def update_recent_file(self, path: str) -> None:
        """更新最近文件列表，保持最新 10 条。"""
        recent = [p for p in self._data.get("recentFiles", []) if p != path]
        recent.insert(0, path)
        self._data["recentFiles"] = recent[:10]
        self.save()

    @Property(str, notify=themeChanged)
    def theme(self) -> str:
        return self._data.get("theme", "system")

    @theme.setter
    def theme(self, value: str) -> None:
        if self._data.get("theme") != value:
            self._data["theme"] = value
            self.themeChanged.emit(value)
            self.save()

    @Property(str, notify=languageChanged)
    def language(self) -> str:
        return self._data.get("language", "auto")

    @language.setter
    def language(self, value: str) -> None:
        if self._data.get("language") != value:
            self._data["language"] = value
            self.languageChanged.emit(value)
            self.save()

    @Property(bool, notify=networkEnabledChanged)
    def networkEnabled(self) -> bool:
        return bool(self._data.get("networkEnabled", False))

    @networkEnabled.setter
    def networkEnabled(self, value: bool) -> None:
        if self._data.get("networkEnabled") != value:
            self._data["networkEnabled"] = value
            self.networkEnabledChanged.emit(value)
            self.save()
