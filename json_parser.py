"""Commercial-ready JSON parsing tool built with PyQt5 and qfluentwidgets.

The module exposes a polished desktop experience for inspecting JSON payloads.
Users can open files, format raw data, explore a structured tree, search
through keys, and copy fully-qualified JSON paths with a single click.  The UI
leans on qfluentwidgets components to provide a professional Fluent Design
appearance suitable for real-world distribution.
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

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
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
    CaptionLabel,
    CardWidget,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
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
        self.resize(1100, 720)
        self.resize(960, 640)

        # Use the fluent design language.
        setTheme(Theme.AUTO)

        self._json_input = QPlainTextEdit(self)
        self._json_input.setPlaceholderText("在此粘贴或键入 JSON 数据…")
        self._json_input.setTabChangesFocus(False)
        self._json_input.setLineWrapMode(QPlainTextEdit.NoWrap)
        self._json_input.setStyleSheet(
            "QPlainTextEdit { font-family: 'Cascadia Code', 'JetBrains Mono', monospace;"
            " font-size: 13px; border-radius: 8px; padding: 12px; }"
        )

        self._tree = QTreeWidget(self)
        self._tree.setHeaderLabels(["键", "值"])
        self._tree.setIndentation(18)
        self._tree.setAlternatingRowColors(True)
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self._tree.header().setSectionResizeMode(1, QHeaderView.Stretch)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        self._tree.itemSelectionChanged.connect(self._on_tree_selection_change)

        self._status_label = CaptionLabel("准备就绪。", self)

        # Controls for displaying and copying JSON paths
        self._path_display = LineEdit(self)
        self._path_display.setPlaceholderText("选择节点后显示完整 JSON 路径")
        self._path_display.setReadOnly(True)
        self._path_display.setClearButtonEnabled(True)

        self._copy_path_button = PrimaryPushButton("复制路径", self)
        self._copy_path_button.setToolTip("复制选中节点的 JSON 路径")
        self._copy_path_button.clicked.connect(self._copy_selected_path)
        self._copy_path_button.setEnabled(False)

        path_bar = QHBoxLayout()
        path_bar.setSpacing(12)
        path_bar.addWidget(self._path_display, 1)
        path_bar.addWidget(self._copy_path_button)

        # Search filter for result tree
        self._filter_input = LineEdit(self)
        self._filter_input.setPlaceholderText("输入关键字过滤解析结果…")
        self._filter_input.setClearButtonEnabled(True)
        self._filter_input.textChanged.connect(self._apply_filter)

        self._tree = QTreeWidget(self)
        self._tree.setHeaderLabels(["键", "值"])
        self._tree.setColumnWidth(0, 280)

        self._status_label = BodyLabel("", self)

        parse_button = PrimaryPushButton("解析", self)
        parse_button.clicked.connect(self._parse_json)

        format_button = PushButton("格式化", self)
        format_button.clicked.connect(self._format_json)

        load_button = PushButton("打开文件", self)
        load_button.clicked.connect(self._open_json_file)

        clear_button = PushButton("清空", self)
        clear_button.clicked.connect(self._clear_all)

        expand_button = PushButton("展开全部", self)
        expand_button.clicked.connect(self._tree.expandAll)

        collapse_button = PushButton("折叠全部", self)
        collapse_button.clicked.connect(self._tree.collapseAll)

        button_bar = QHBoxLayout()
        button_bar.setSpacing(10)
        button_bar.addWidget(parse_button)
        button_bar.addWidget(format_button)
        button_bar.addWidget(load_button)
        button_bar.addWidget(clear_button)
        button_bar.addStretch(1)
        button_bar.addWidget(expand_button)
        button_bar.addWidget(collapse_button)

        input_card = CardWidget(self)
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(16)
        input_layout.addWidget(BodyLabel("输入 JSON 数据"))
        input_layout.addWidget(self._json_input, 1)
        input_layout.addLayout(button_bar)

        output_card = CardWidget(self)
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(12)
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        header_row.addWidget(BodyLabel("解析结果"))
        header_row.addStretch(1)
        header_row.addWidget(self._filter_input)
        output_layout.addLayout(header_row)
        output_layout.addWidget(self._tree, 1)
        output_layout.addLayout(path_bar)
        output_layout.addWidget(self._status_label)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(input_card)
        splitter.addWidget(output_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)

        intro_card = CardWidget(self)
        intro_layout = QVBoxLayout(intro_card)
        intro_layout.setContentsMargins(20, 16, 20, 20)
        intro_layout.setSpacing(6)
        intro_layout.addWidget(CaptionLabel("专业级 JSON 工具"))
        intro_layout.addWidget(
            BodyLabel(
                "打开文件或粘贴 JSON 文本，快速格式化、检索并复制任意节点路径。"
            )
        )

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(intro_card)
        layout.addWidget(splitter, 1)
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
        self._status_label.setText(f"已加载文件：{file_path.name}")
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
        self._status_label.setText("解析成功，支持搜索与复制路径。")
        self._status_label.setText("解析成功！")
        InfoBar.success(
            title="解析完成",
            content="JSON 数据解析成功。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=1500,
        )

    def _clear_all(self) -> None:
        """Reset editor, tree and helper widgets."""

        self._json_input.clear()
        self._tree.clear()
        self._path_display.clear()
        self._filter_input.clear()
        self._copy_path_button.setEnabled(False)
        self._status_label.setText("已清空所有内容。")

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
        self._path_display.clear()
        self._copy_path_button.setEnabled(False)

        root_item = self._create_tree_item("$", data, "$")
        if root_item is not None:
            self._tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)
            self._tree.expandToDepth(1)

        if self._filter_input.text().strip():
            self._apply_filter(self._filter_input.text())
        else:
            self._reset_filter()

    def _create_tree_item(self, key: str, value: Any, path: str) -> QTreeWidgetItem | None:
        """Create a tree item for a JSON entry."""

        if isinstance(value, dict):
            item = QTreeWidgetItem([str(key), self._describe_value(value)])
            item.setData(0, Qt.UserRole, path)
            for child_key, child_value in value.items():
                child_path = f"{path}.{child_key}" if path != "$" else f"$.{child_key}"
                child_item = self._create_tree_item(child_key, child_value, child_path)
                if child_item is not None:
                    item.addChild(child_item)
        elif isinstance(value, list):
            item = QTreeWidgetItem([str(key), self._describe_value(value)])
            item.setData(0, Qt.UserRole, path)
            for index, child_value in enumerate(value):
                child_path = f"{path}[{index}]"
                child_item = self._create_tree_item(f"[{index}]", child_value, child_path)
                if child_item is not None:
                    item.addChild(child_item)
        else:
            text = self._format_scalar(value)
            item = QTreeWidgetItem([str(key), text])
            item.setData(0, Qt.UserRole, path)
        return item

    def _describe_value(self, value: Any) -> str:
        """Return a human friendly description for containers."""

        if isinstance(value, dict):
            return f"对象（{len(value)} 项）"
        if isinstance(value, list):
            return f"数组（{len(value)} 项）"
        return self._format_scalar(value)

    def _format_scalar(self, value: Any) -> str:
        """Format primitive JSON values with proper localisation."""

        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(value, ensure_ascii=False)

    def _show_tree_context_menu(self, position: QPoint) -> None:
        """Provide context menu for copying path or value."""

        item = self._tree.itemAt(position)
        if item is None:
            return

        menu = QMenu(self)
        copy_path_action = QAction("复制路径", self)
        copy_path_action.triggered.connect(self._copy_selected_path)
        menu.addAction(copy_path_action)

        copy_value_action = QAction("复制值", self)
        copy_value_action.triggered.connect(self._copy_selected_value)
        menu.addAction(copy_value_action)

        menu.exec_(self._tree.viewport().mapToGlobal(position))

    def _on_tree_selection_change(self) -> None:
        """Update path display whenever the selection changes."""

        items = self._tree.selectedItems()
        if not items:
            self._path_display.clear()
            self._copy_path_button.setEnabled(False)
            return

        item = items[0]
        path = item.data(0, Qt.UserRole)
        if path:
            self._path_display.setText(path)
            self._copy_path_button.setEnabled(True)

    def _copy_selected_path(self) -> None:
        """Copy the JSON path of the selected node to clipboard."""

        items = self._tree.selectedItems()
        if not items:
            return

        path = items[0].data(0, Qt.UserRole)
        if not path:
            return

        QGuiApplication.clipboard().setText(path)
        InfoBar.success(
            title="已复制路径",
            content=f"JSON 路径 {path} 已复制到剪贴板。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=1200,
        )

    def _copy_selected_value(self) -> None:
        """Copy the current node value to clipboard."""

        items = self._tree.selectedItems()
        if not items:
            return

        value = items[0].text(1)
        if not value:
            return

        QGuiApplication.clipboard().setText(value)
        InfoBar.success(
            title="已复制值",
            content="节点值已复制到剪贴板。",
            parent=self,
            position=InfoBarPosition.TOP,
            duration=1200,
        )

    def _apply_filter(self, text: str) -> None:
        """Filter the tree view based on the given keyword."""

        keyword = text.strip().lower()
        if not keyword:
            self._reset_filter()
            return

        self._tree.setUpdatesEnabled(False)
        for index in range(self._tree.topLevelItemCount()):
            self._filter_item(self._tree.topLevelItem(index), keyword)
        self._tree.setUpdatesEnabled(True)

    def _filter_item(self, item: QTreeWidgetItem, keyword: str) -> bool:
        """Recursively hide nodes that do not match the keyword."""

        match = keyword in item.text(0).lower() or keyword in item.text(1).lower()
        child_match = False
        for idx in range(item.childCount()):
            child_visible = self._filter_item(item.child(idx), keyword)
            child_match = child_match or child_visible

        visible = match or child_match
        item.setHidden(not visible)
        item.setExpanded(visible and item.childCount() > 0)
        return visible

    def _reset_filter(self) -> None:
        """Show all items when clearing the search box."""

        self._tree.setUpdatesEnabled(False)
        for index in range(self._tree.topLevelItemCount()):
            self._show_item_recursive(self._tree.topLevelItem(index))
        self._tree.setUpdatesEnabled(True)

    def _show_item_recursive(self, item: QTreeWidgetItem) -> None:
        item.setHidden(False)
        item.setExpanded(item.childCount() > 0)
        for idx in range(item.childCount()):
            self._show_item_recursive(item.child(idx))

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

