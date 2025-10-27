"""Commercial-ready JSON parsing tool built with PyQt5 and qfluentwidgets.

The module exposes a polished desktop experience for inspecting JSON payloads.
Users can open files, format raw data, explore a structured tree, search
through keys, and copy fully-qualified JSON paths with a single click.  The UI
leans on qfluentwidgets components to provide a professional Fluent Design
appearance suitable for real-world distribution.
"""

import json
from pathlib import Path
from typing import Any, Optional

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QColor, QGuiApplication
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QGraphicsDropShadowEffect,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    Theme,
    setTheme,
)


class JsonParserWindow(QMainWindow):
    """Main window of the JSON parsing tool."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("JSON 数据洞察工具")
        self.resize(1180, 760)

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
        self._tree.setUniformRowHeights(True)
        self._tree.setAnimated(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        self._tree.itemSelectionChanged.connect(self._on_tree_selection_change)

        self._status_label = CaptionLabel("准备就绪。", self)
        self._status_label.setObjectName("statusLabel")

        # Controls for displaying and copying JSON paths
        self._path_display = LineEdit(self)
        self._path_display.setPlaceholderText("选择节点后显示完整 JSON 路径")
        self._path_display.setReadOnly(True)
        self._path_display.setClearButtonEnabled(True)

        self._copy_path_button = PrimaryPushButton("复制路径", self)
        self._copy_path_button.setToolTip("复制选中节点的 JSON 路径")
        self._copy_path_button.clicked.connect(self._copy_selected_path)
        self._copy_path_button.setEnabled(False)

        self._copy_value_button = PushButton("复制值", self)
        self._copy_value_button.setToolTip("复制选中节点的原始值")
        self._copy_value_button.clicked.connect(self._copy_selected_value)
        self._copy_value_button.setEnabled(False)

        self._value_preview = QPlainTextEdit(self)
        self._value_preview.setObjectName("valuePreview")
        self._value_preview.setReadOnly(True)
        self._value_preview.setFocusPolicy(Qt.NoFocus)
        self._value_preview.setFixedHeight(160)
        self._value_preview.setPlainText("在左侧树形结构中选择节点以查看其值和路径…")
        self._value_preview.setStyleSheet(
            "QPlainTextEdit#valuePreview {"
            " border-radius: 10px;"
            " border: 1px solid rgba(120, 120, 120, 40);"
            " background-color: rgba(255, 255, 255, 210);"
            " font-family: 'Cascadia Code', 'JetBrains Mono', monospace;"
            " font-size: 12px;"
            " padding: 10px;"
            " color: rgba(30, 30, 30, 200);"
            " }"
        )

        path_bar = QHBoxLayout()
        path_bar.setSpacing(12)
        path_bar.addWidget(self._path_display, 1)
        path_bar.addWidget(self._copy_path_button)

        # Search filter for result tree
        self._filter_input = LineEdit(self)
        self._filter_input.setPlaceholderText("输入关键字过滤解析结果…")
        self._filter_input.setClearButtonEnabled(True)
        self._filter_input.textChanged.connect(self._apply_filter)
        self._filter_input.setObjectName("filterBox")

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

        for button, icon in (
            (parse_button, FluentIcon.PLAY),
            (format_button, FluentIcon.CODE),
            (load_button, FluentIcon.FOLDER_OPEN),
            (clear_button, FluentIcon.DELETE),
            (expand_button, FluentIcon.ZOOM_IN),
            (collapse_button, FluentIcon.ZOOM_OUT),
            (self._copy_path_button, FluentIcon.LINK),
            (self._copy_value_button, FluentIcon.COPY),
        ):
            button.setIcon(icon.icon())
            button.setMinimumHeight(36)

        button_bar = QHBoxLayout()
        button_bar.setSpacing(14)
        button_bar.addWidget(parse_button)
        button_bar.addWidget(format_button)
        button_bar.addWidget(load_button)
        button_bar.addWidget(clear_button)
        button_bar.addStretch(1)
        button_bar.addWidget(expand_button)
        button_bar.addWidget(collapse_button)

        input_card = CardWidget(self)
        input_card.setObjectName("inputCard")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(16)
        input_title = BodyLabel("输入 JSON 数据")
        input_title.setObjectName("cardTitle")
        input_layout.addWidget(input_title)
        input_layout.addWidget(self._json_input, 1)
        input_layout.addLayout(button_bar)

        output_card = CardWidget(self)
        output_card.setObjectName("outputCard")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 20, 20, 20)
        output_layout.setSpacing(12)
        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        result_title = BodyLabel("解析结果")
        result_title.setObjectName("cardTitle")
        header_row.addWidget(result_title)
        header_row.addStretch(1)
        header_row.addWidget(self._filter_input)
        output_layout.addLayout(header_row)
        output_layout.addWidget(self._tree, 1)

        detail_card = CardWidget(self)
        detail_card.setObjectName("detailCard")
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(18, 18, 18, 18)
        detail_layout.setSpacing(12)

        path_label_row = QHBoxLayout()
        path_label_row.addWidget(CaptionLabel("JSON 路径"))
        path_label_row.addStretch(1)
        detail_layout.addLayout(path_label_row)

        detail_layout.addLayout(path_bar)

        value_label_row = QHBoxLayout()
        value_label = CaptionLabel("节点值")
        value_label_row.addWidget(value_label)
        value_label_row.addStretch(1)
        value_label_row.addWidget(self._copy_value_button)
        detail_layout.addLayout(value_label_row)
        detail_layout.addWidget(self._value_preview)

        output_layout.addWidget(detail_card)
        output_layout.addWidget(self._status_label)

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(input_card)
        splitter.addWidget(output_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        splitter.setChildrenCollapsible(False)

        hero_card = CardWidget(self)
        hero_card.setObjectName("heroCard")
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(10)

        hero_title = BodyLabel("JSON 数据洞察工具")
        hero_title.setObjectName("heroTitle")
        hero_subtitle = CaptionLabel(
            "Fluent Design 风格的专业解析器，支持格式化、搜索、复制路径与值。"
        )
        hero_subtitle.setObjectName("heroSubtitle")
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_subtitle)

        central = QWidget(self)
        central.setObjectName("centralWidget")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(hero_card)
        layout.addWidget(splitter, 1)

        self.setCentralWidget(central)
        self._apply_card_shadows(hero_card, input_card, output_card, detail_card)
        self._apply_global_styles()

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
        self._copy_value_button.setEnabled(False)
        self._value_preview.setPlainText("在左侧树形结构中选择节点以查看其值和路径…")
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
        self._copy_value_button.setEnabled(False)
        self._value_preview.setPlainText("在左侧树形结构中选择节点以查看其值和路径…")

        root_item = self._create_tree_item("$", data, "$")
        if root_item is not None:
            self._tree.addTopLevelItem(root_item)
            root_item.setExpanded(True)
            self._tree.expandToDepth(1)

        if self._filter_input.text().strip():
            self._apply_filter(self._filter_input.text())
        else:
            self._reset_filter()
        self._status_label.setText(self._summarize_data(data))

    def _create_tree_item(
        self, key: str, value: Any, path: str
    ) -> Optional[QTreeWidgetItem]:
        """Create a tree item for a JSON entry."""

        if isinstance(value, dict):
            item = QTreeWidgetItem([str(key), self._describe_value(value)])
            item.setData(0, Qt.UserRole, path)
            item.setData(0, Qt.UserRole + 1, value)
            for child_key, child_value in value.items():
                child_path = f"{path}.{child_key}" if path != "$" else f"$.{child_key}"
                child_item = self._create_tree_item(child_key, child_value, child_path)
                if child_item is not None:
                    item.addChild(child_item)
        elif isinstance(value, list):
            item = QTreeWidgetItem([str(key), self._describe_value(value)])
            item.setData(0, Qt.UserRole, path)
            item.setData(0, Qt.UserRole + 1, value)
            for index, child_value in enumerate(value):
                child_path = f"{path}[{index}]"
                child_item = self._create_tree_item(f"[{index}]", child_value, child_path)
                if child_item is not None:
                    item.addChild(child_item)
        else:
            text = self._format_scalar(value)
            item = QTreeWidgetItem([str(key), text])
            item.setData(0, Qt.UserRole, path)
            item.setData(0, Qt.UserRole + 1, value)
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
            self._copy_value_button.setEnabled(False)
            self._value_preview.setPlainText("在左侧树形结构中选择节点以查看其值和路径…")
            return

        item = items[0]
        path = item.data(0, Qt.UserRole)
        if path:
            self._path_display.setText(path)
            self._copy_path_button.setEnabled(True)
        value = item.data(0, Qt.UserRole + 1)
        formatted = (
            json.dumps(value, indent=4, ensure_ascii=False)
            if isinstance(value, (dict, list))
            else self._format_scalar(value)
        )
        self._value_preview.setPlainText(formatted)
        self._copy_value_button.setEnabled(True)

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

        value = items[0].data(0, Qt.UserRole + 1)
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False)
        else:
            text = self._format_scalar(value)

        QGuiApplication.clipboard().setText(text)
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
        self._status_label.setText(f"共找到 {self._count_visible_items()} 个匹配节点。")

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
        self._status_label.setText("已显示全部节点。")

    def _show_item_recursive(self, item: QTreeWidgetItem) -> None:
        item.setHidden(False)
        item.setExpanded(item.childCount() > 0)
        for idx in range(item.childCount()):
            self._show_item_recursive(item.child(idx))

    def _count_visible_items(self) -> int:
        def _count(item: QTreeWidgetItem) -> int:
            if item.isHidden():
                return 0
            total = 1
            for idx in range(item.childCount()):
                total += _count(item.child(idx))
            return total

        total_visible = 0
        for index in range(self._tree.topLevelItemCount()):
            total_visible += _count(self._tree.topLevelItem(index))
        return total_visible

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

    # ------------------------------------------------------------------
    # Styling helpers
    # ------------------------------------------------------------------
    def _apply_card_shadows(self, *cards: CardWidget) -> None:
        for card in cards:
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(28)
            shadow.setXOffset(0)
            shadow.setYOffset(12)
            shadow.setColor(QColor(20, 20, 20, 35))
            card.setGraphicsEffect(shadow)

    def _apply_global_styles(self) -> None:
        self.setStyleSheet(
            "#centralWidget {"
            " background: #f3f5fb;"
            " }"
            "CardWidget#heroCard {"
            " background: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            " stop:0 #4f9dff, stop:1 #6d5bff);"
            " border-radius: 22px;"
            " color: white;"
            " }"
            "BodyLabel#heroTitle { font-size: 26px; font-weight: 600; }"
            "CaptionLabel#heroSubtitle { font-size: 14px; color: rgba(255, 255, 255, 200); }"
            "CardWidget#inputCard, CardWidget#outputCard {"
            " border-radius: 20px;"
            " background-color: rgba(255, 255, 255, 235);"
            " }"
            "CardWidget#detailCard {"
            " border-radius: 16px;"
            " background-color: rgba(248, 249, 254, 230);"
            " }"
            "LineEdit {"
            " border-radius: 10px;"
            " padding: 6px 12px;"
            " font-size: 13px;"
            " }"
            "LineEdit#filterBox { min-width: 240px; }"
            "BodyLabel#cardTitle { font-size: 16px; font-weight: 600; }"
            "QTreeWidget {"
            " background: rgba(255, 255, 255, 240);"
            " border-radius: 12px;"
            " padding: 4px;"
            " }"
            "QTreeWidget::item { height: 28px; }"
            "PrimaryPushButton, PushButton {"
            " border-radius: 18px;"
            " padding: 6px 14px;"
            " }"
            "CaptionLabel#statusLabel { color: rgba(70, 80, 110, 180); }"
        )

    def _summarize_data(self, data: Any) -> str:
        if isinstance(data, dict):
            return f"解析成功：根对象包含 {len(data)} 个键。"
        if isinstance(data, list):
            return f"解析成功：根数组包含 {len(data)} 个元素。"
        return "解析成功：根节点为原始值。"


def main() -> None:
    """Entry point to run the JSON parsing tool."""

    import sys

    app = QApplication(sys.argv)
    window = JsonParserWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

