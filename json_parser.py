"""Simple JSON parsing tool built with PyQt5 and qfluentwidgets.

This module provides a small desktop utility that can load JSON data from a
file or accept manual input, parse it and visualise the structure in a tree
view.  It demonstrates how qfluentwidgets can be combined with standard Qt
widgets to quickly build a fluent style user interface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
)

from qfluentwidgets import (
    BodyLabel,
    InfoBar,
    InfoBarPosition,
    PrimaryPushButton,
    Theme,
    setTheme,
)


class JsonParserWindow(QMainWindow):
    """Main window of the JSON parsing tool."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("JSON 数据解析工具")
        self.resize(960, 640)

        # Use the fluent design language.
        setTheme(Theme.AUTO)

        self._json_input = QPlainTextEdit(self)
        self._json_input.setPlaceholderText("在此粘贴或键入 JSON 数据…")
        self._json_input.setTabChangesFocus(False)

        self._tree = QTreeWidget(self)
        self._tree.setHeaderLabels(["键", "值"])
        self._tree.setColumnWidth(0, 280)

        self._status_label = BodyLabel("", self)

        parse_button = PrimaryPushButton("解析", self)
        parse_button.clicked.connect(self._parse_json)

        load_button = PrimaryPushButton("打开文件", self)
        load_button.clicked.connect(self._open_json_file)

        format_button = PrimaryPushButton("格式化", self)
        format_button.clicked.connect(self._format_json)

        button_bar = QHBoxLayout()
        button_bar.setSpacing(12)
        button_bar.addWidget(parse_button)
        button_bar.addWidget(format_button)
        button_bar.addWidget(load_button)
        button_bar.addStretch(1)

        input_panel = QWidget(self)
        input_layout = QVBoxLayout(input_panel)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)
        input_layout.addWidget(BodyLabel("输入", self))
        input_layout.addWidget(self._json_input)
        input_layout.addLayout(button_bar)

        output_panel = QWidget(self)
        output_layout = QVBoxLayout(output_panel)
        output_layout.setContentsMargins(0, 0, 0, 0)
        output_layout.setSpacing(8)
        output_layout.addWidget(BodyLabel("解析结果", self))
        output_layout.addWidget(self._tree)
        output_layout.addWidget(self._status_label)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(input_panel)
        splitter.addWidget(output_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(splitter)

        self.setCentralWidget(central)

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------
    def _open_json_file(self) -> None:
        """Open a JSON file from disk and load its content."""

        dialog = QFileDialog(self, "选择 JSON 文件")
        dialog.setFileMode(QFileDialog.ExistingFile)
        dialog.setNameFilter("JSON 文件 (*.json);;所有文件 (*.*)")
        if dialog.exec_() != QFileDialog.Accepted:
            return

        file_path = Path(dialog.selectedFiles()[0])
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as exc:  # pragma: no cover - UI feedback
            self._show_error(f"无法读取文件: {exc}")
            return

        self._json_input.setPlainText(content)
        self._status_label.setText(f"已加载: {file_path.name}")

    def _parse_json(self) -> None:
        """Parse JSON from the text box and fill the tree widget."""

        raw = self._json_input.toPlainText().strip()
        if not raw:
            self._show_error("请输入 JSON 数据后再进行解析。")
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._show_error(f"JSON 解析失败: {exc.msg} (行 {exc.lineno}, 列 {exc.colno})")
            return

        self._populate_tree(data)
        self._status_label.setText("解析成功！")
        InfoBar.success(
            title="解析完成",
            content="JSON 数据解析成功。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=1500,
        )

    def _format_json(self) -> None:
        """Format JSON text with indentation to improve readability."""

        raw = self._json_input.toPlainText().strip()
        if not raw:
            self._show_error("没有可以格式化的 JSON 内容。")
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._show_error(f"JSON 无法格式化: {exc.msg} (行 {exc.lineno}, 列 {exc.colno})")
            return

        formatted = json.dumps(data, indent=4, ensure_ascii=False)
        self._json_input.setPlainText(formatted)
        self._status_label.setText("已格式化 JSON 文本。")
        InfoBar.success(
            title="格式化完成",
            content="JSON 已重新排版。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=1500,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _populate_tree(self, data: Any) -> None:
        """Populate the tree widget with JSON data."""

        self._tree.clear()
        root_item = self._create_tree_item("root", data)
        if root_item is not None:
            self._tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)

    def _create_tree_item(self, key: str, value: Any) -> QTreeWidgetItem | None:
        """Create a tree item for a JSON entry."""

        if isinstance(value, dict):
            item = QTreeWidgetItem([str(key), "对象"])
            for child_key, child_value in value.items():
                child_item = self._create_tree_item(child_key, child_value)
                if child_item is not None:
                    item.addChild(child_item)
        elif isinstance(value, list):
            item = QTreeWidgetItem([str(key), f"数组[{len(value)}]"])
            for index, child_value in enumerate(value):
                child_item = self._create_tree_item(f"[{index}]", child_value)
                if child_item is not None:
                    item.addChild(child_item)
        else:
            text = json.dumps(value, ensure_ascii=False)
            item = QTreeWidgetItem([str(key), text])
        return item

    def _show_error(self, message: str) -> None:
        """Display an error message using InfoBar and a fallback message box."""

        InfoBar.error(
            title="发生错误",
            content=message,
            parent=self,
            position=InfoBarPosition.TOP,
            duration=2500,
        )

        # Provide a fallback dialog in case InfoBar is hidden or dismissed.
        QMessageBox.critical(self, "错误", message)


def main() -> None:
    """Entry point to run the JSON parsing tool."""

    import sys

    app = QApplication(sys.argv)
    window = JsonParserWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

