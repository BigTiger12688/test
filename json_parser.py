"""Commercial-ready JSON parsing tool with multi-workspace support."""

import json
from pathlib import Path
from string import Template
from typing import Any, Dict, Optional

from PyQt5.QtCore import QPoint, QRect, QRectF, QSize, Qt, pyqtSignal
from PyQt5.QtGui import (
    QColor,
    QGuiApplication,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QBrush,
    QPen,
    QTextFormat,
)
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
    QTabBar,
    QTextEdit,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from qfluentwidgets import (
    BodyLabel,
    CaptionLabel,
    CardWidget,
    ComboBox,
    FluentIcon,
    LineEdit,
    PrimaryPushButton,
    PushButton,
    Theme,
    setTheme,
)


def resolve_fluent_icon(
    primary: str,
    fallback: str = "FOLDER_ADD",
    color: Optional[QColor] = None,
):
    """Return a QIcon for the requested Fluent icon, falling back when missing."""

    icon = getattr(FluentIcon, primary, None)
    if icon is None:
        icon = getattr(FluentIcon, fallback, None)
    if icon is None:
        icon = FluentIcon.ADD
    if color is not None:
        try:
            return icon.icon(color=color)
        except TypeError:
            # Older qfluentwidgets versions may not accept the color keyword.
            pass
    return icon.icon()


class LineNumberArea(QWidget):
    """Auxiliary widget for rendering line numbers next to the editor."""

    def __init__(self, editor: "CodeEditor") -> None:
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self) -> QSize:  # type: ignore[override]
        return QSize(self._editor.line_number_area_width(), 0)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        self._editor.paint_line_number_area(event)


class CodeEditor(QPlainTextEdit):
    """Plain text edit with line numbers and current line highlight."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._line_number_area = LineNumberArea(self)
        self._current_theme = Theme.LIGHT
        self._apply_theme_stylesheet()

        self.setTabChangesFocus(False)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setPlaceholderText("在此粘贴或键入 JSON 数据…")

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

    # ------------------------------------------------------------------
    # Painting helpers
    # ------------------------------------------------------------------
    def line_number_area_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return self.fontMetrics().horizontalAdvance("9" * digits) + 24

    def _update_line_number_area_width(self, _new_block_count: int) -> None:
        margin = self.line_number_area_width()
        self.setViewportMargins(margin, 0, 0, 0)

    def _update_line_number_area(self, rect, dy: int) -> None:
        if dy:
            self._line_number_area.scroll(0, dy)
        else:
            self._line_number_area.update(0, rect.y(), self._line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        cr = self.contentsRect()
        self._line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def paint_line_number_area(self, event) -> None:
        painter = QPainter(self._line_number_area)
        painter.setRenderHint(QPainter.Antialiasing)
        palette = self._palette_for_theme()
        full_rect = self._line_number_area.rect()
        radius = 12

        background_path = QPainterPath()
        background_path.moveTo(full_rect.right(), full_rect.top())
        background_path.lineTo(full_rect.left() + radius, full_rect.top())
        background_path.quadTo(full_rect.left(), full_rect.top(), full_rect.left(), full_rect.top() + radius)
        background_path.lineTo(full_rect.left(), full_rect.bottom() - radius)
        background_path.quadTo(full_rect.left(), full_rect.bottom(), full_rect.left() + radius, full_rect.bottom())
        background_path.lineTo(full_rect.right(), full_rect.bottom())
        background_path.closeSubpath()
        painter.fillPath(background_path, palette["background"])

        border_pen = QPen(palette["border"])
        border_pen.setWidthF(1.0)
        painter.setPen(border_pen)
        painter.drawLine(full_rect.left(), full_rect.top() + radius, full_rect.left(), full_rect.bottom() - radius)
        painter.drawArc(full_rect.left(), full_rect.top(), radius * 2, radius * 2, 90 * 16, 90 * 16)
        painter.drawArc(
            full_rect.left(), full_rect.bottom() - radius * 2, radius * 2, radius * 2, 180 * 16, 90 * 16
        )

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(palette["foreground"])
                fm = self.fontMetrics()
                x = self.line_number_area_width() - 12 - fm.horizontalAdvance(number)
                painter.drawText(x, top, self.line_number_area_width(), fm.height(), Qt.AlignLeft, number)
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

        border_color = palette["border"]
        painter.setPen(border_color)
        right = event.rect().right()
        painter.drawLine(right - 1, event.rect().top(), right - 1, event.rect().bottom())

    def _highlight_current_line(self) -> None:
        selection = QTextEdit.ExtraSelection()
        palette = self._palette_for_theme()
        selection.format.setBackground(palette["highlight"])
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()
        selection.cursor.clearSelection()
        self.setExtraSelections([selection])

    def _palette_for_theme(self) -> Dict[str, QColor]:
        if self._current_theme == Theme.DARK:
            return {
                "background": QColor(35, 37, 47),
                "foreground": QColor(140, 145, 165),
                "highlight": QColor(58, 60, 70, 160),
                "border": QColor(84, 94, 120, 180),
            }
        return {
            "background": QColor(255, 255, 255),
            "foreground": QColor(120, 125, 140),
            "highlight": QColor(223, 229, 255),
            "border": QColor(200, 210, 230, 150),
        }

    def set_theme(self, theme: Theme) -> None:
        self._current_theme = theme
        self._apply_theme_stylesheet()
        self._highlight_current_line()
        self._line_number_area.update()

    def _apply_theme_stylesheet(self) -> None:
        if self._current_theme == Theme.DARK:
            background = "#23252f"
            foreground = "rgba(222, 226, 235, 220)"
            border = "rgba(84, 94, 120, 180)"
            selection_bg = "rgba(86, 99, 135, 180)"
            selection_fg = "rgba(245, 248, 255, 230)"
        else:
            background = "#ffffff"
            foreground = "rgba(43, 48, 60, 220)"
            border = "rgba(200, 210, 230, 150)"
            selection_bg = "rgba(135, 169, 255, 120)"
            selection_fg = "rgba(20, 25, 38, 220)"

        self.setStyleSheet(
            "QPlainTextEdit {"
            " font-family: 'Cascadia Code', 'JetBrains Mono', monospace;"
            " font-size: 13px;"
            " border-radius: 12px;"
            " border-top-left-radius: 0px;"
            " border-bottom-left-radius: 0px;"
            " padding: 12px;"
            f" background-color: {background};"
            f" color: {foreground};"
            f" border: 1px solid {border};"
            " border-left: 0px;"
            f" selection-background-color: {selection_bg};"
            f" selection-color: {selection_fg};"
            " }"
        )
        self._line_number_area.setStyleSheet(
            "QWidget {"
            f" background-color: {background};"
            f" color: {foreground};"
            f" border: 1px solid {border};"
            " border-right: 0px;"
            " border-top-right-radius: 0px;"
            " border-bottom-right-radius: 0px;"
            " border-top-left-radius: 12px;"
            " border-bottom-left-radius: 12px;"
            " }"
        )


class GradientHeroCard(CardWidget):
    """Hero banner with theme-aware gradient rendering."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("heroCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self._current_theme = Theme.LIGHT
        self._light_colors = (QColor(79, 157, 255), QColor(109, 91, 255))
        self._dark_colors = (QColor(75, 91, 220), QColor(58, 122, 254))

    def set_theme(self, theme: Theme) -> None:
        if theme == self._current_theme:
            return
        self._current_theme = theme
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        rect = QRectF(self.rect().adjusted(1, 1, -1, -1))
        path = QPainterPath()
        radius = 22.0
        path.addRoundedRect(rect, radius, radius)

        start_color, end_color = (
            self._dark_colors if self._current_theme == Theme.DARK else self._light_colors
        )
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        gradient.setColorAt(0.0, start_color)
        gradient.setColorAt(1.0, end_color)
        painter.fillPath(path, gradient)


class WorkspaceTabBar(QTabBar):
    """Custom tab bar providing themed close buttons and spacing."""

    tabCloseRequested = pyqtSignal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._theme = Theme.LIGHT
        self.setDocumentMode(True)
        self.setExpanding(False)
        self.setMovable(True)
        self.setElideMode(Qt.ElideRight)
        self.setUsesScrollButtons(True)

    def set_theme(self, theme: Theme) -> None:
        if theme == self._theme:
            return
        self._theme = theme
        self._refresh_close_buttons()

    def tabInserted(self, index: int) -> None:  # type: ignore[override]
        super().tabInserted(index)
        self._install_close_button(index)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _emit_close_for_button(self, button: QToolButton) -> None:
        position = button.mapTo(self, button.rect().center())
        index = self.tabAt(position)
        if index != -1:
            self.tabCloseRequested.emit(index)

    def _install_close_button(self, index: int) -> None:
        button = QToolButton(self)
        button.setCursor(Qt.PointingHandCursor)
        button.setAutoRaise(True)
        button.setText("✕")
        button.setObjectName("workspaceTabCloseButton")
        button.clicked.connect(lambda _=False, b=button: self._emit_close_for_button(b))
        self._style_close_button(button)
        self.setTabButton(index, QTabBar.RightSide, button)

    def _refresh_close_buttons(self) -> None:
        for index in range(self.count()):
            button = self.tabButton(index, QTabBar.RightSide)
            if isinstance(button, QToolButton):
                self._style_close_button(button)

    def _style_close_button(self, button: QToolButton) -> None:
        if self._theme == Theme.DARK:
            color = "rgba(220, 225, 238, 210)"
            hover_bg = "rgba(120, 140, 210, 90)"
            press_bg = "rgba(120, 140, 210, 130)"
        else:
            color = "rgba(60, 70, 92, 210)"
            hover_bg = "rgba(100, 140, 255, 70)"
            press_bg = "rgba(100, 140, 255, 110)"

        button.setStyleSheet(
            f"""
            QToolButton#workspaceTabCloseButton {{
                border: none;
                font-size: 14px;
                padding: 0px;
                color: {color};
            }}
            QToolButton#workspaceTabCloseButton:hover {{
                background-color: {hover_bg};
                border-radius: 10px;
            }}
            QToolButton#workspaceTabCloseButton:pressed {{
                background-color: {press_bg};
                border-radius: 10px;
            }}
            """
        )


class JsonWorkspace(QWidget):
    """Encapsulates a single JSON parsing workspace."""

    titleChanged = pyqtSignal(str)

    COLOR_SCHEMES: Dict[str, Dict[str, Dict[str, QColor]]] = {
        "清新配色": {
            "light": {
                "object": QColor(67, 140, 255),
                "array": QColor(52, 201, 121),
                "string": QColor(232, 99, 132),
                "number": QColor(255, 170, 76),
                "bool": QColor(143, 108, 255),
                "null": QColor(148, 165, 180),
                "default": QColor(50, 52, 58),
            },
            "dark": {
                "object": QColor(144, 185, 255),
                "array": QColor(132, 226, 180),
                "string": QColor(255, 168, 198),
                "number": QColor(255, 205, 146),
                "bool": QColor(196, 171, 255),
                "null": QColor(172, 184, 201),
                "default": QColor(224, 228, 238),
            },
        },
        "绚丽配色": {
            "light": {
                "object": QColor(255, 100, 124),
                "array": QColor(72, 202, 228),
                "string": QColor(255, 206, 84),
                "number": QColor(149, 125, 173),
                "bool": QColor(84, 160, 255),
                "null": QColor(205, 214, 244),
                "default": QColor(30, 30, 40),
            },
            "dark": {
                "object": QColor(255, 149, 167),
                "array": QColor(140, 226, 238),
                "string": QColor(255, 217, 120),
                "number": QColor(197, 171, 230),
                "bool": QColor(148, 193, 255),
                "null": QColor(209, 218, 238),
                "default": QColor(226, 229, 236),
            },
        },
        "专业配色": {
            "light": {
                "object": QColor(82, 121, 255),
                "array": QColor(42, 157, 143),
                "string": QColor(231, 111, 81),
                "number": QColor(244, 162, 97),
                "bool": QColor(38, 70, 83),
                "null": QColor(131, 149, 167),
                "default": QColor(33, 37, 41),
            },
            "dark": {
                "object": QColor(165, 195, 255),
                "array": QColor(118, 205, 194),
                "string": QColor(241, 155, 128),
                "number": QColor(255, 204, 153),
                "bool": QColor(120, 150, 166),
                "null": QColor(180, 195, 210),
                "default": QColor(218, 224, 235),
            },
        },
    }

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("workspacePage")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._current_scheme = "清新配色"
        self._theme = Theme.LIGHT
        self._build_ui()
        self._connect_signals()
        self.apply_color_scheme(self._current_scheme)
        self.apply_theme(self._theme)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        self._editor = CodeEditor(self)

        self._tree = QTreeWidget(self)
        self._tree.setHeaderLabels(["键", "值"])
        self._tree.setIndentation(18)
        self._tree.setAlternatingRowColors(True)
        header = self._tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self._tree.setExpandsOnDoubleClick(True)
        self._tree.setUniformRowHeights(True)
        self._tree.setAnimated(True)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)

        self._path_display = LineEdit(self)
        self._path_display.setPlaceholderText("选择节点后显示完整 JSON 路径")
        self._path_display.setReadOnly(True)
        self._path_display.setClearButtonEnabled(True)

        self._copy_path_button = PrimaryPushButton("复制路径", self)
        self._copy_path_button.setIcon(FluentIcon.LINK.icon())
        self._copy_path_button.setEnabled(False)

        self._copy_value_button = PushButton("复制值", self)
        self._copy_value_button.setIcon(FluentIcon.COPY.icon())
        self._copy_value_button.setEnabled(False)

        self._value_preview = QPlainTextEdit(self)
        self._value_preview.setObjectName("valuePreview")
        self._value_preview.setReadOnly(True)
        self._value_preview.setFocusPolicy(Qt.NoFocus)
        self._value_preview.setMinimumHeight(200)
        self._value_preview.setStyleSheet(
            "QPlainTextEdit#valuePreview {"
            " font-family: 'Cascadia Code', 'JetBrains Mono', monospace;"
            " font-size: 12px;"
            " border-radius: 10px;"
            " padding: 10px;"
            " }"
        )
        self._value_preview.setPlainText("选择节点以查看完整的 JSON 值…")

        self._filter_input = LineEdit(self)
        self._filter_input.setPlaceholderText("输入关键字过滤解析结果…")
        self._filter_input.setClearButtonEnabled(True)
        self._filter_input.setObjectName("filterBox")

        self._color_combo = ComboBox(self)
        for name in self.COLOR_SCHEMES:
            self._color_combo.addItem(name)
        self._color_combo.setCurrentText(self._current_scheme)

        self._parse_button = PrimaryPushButton("解析", self)
        self._parse_button.setIcon(FluentIcon.PLAY.icon())
        self._format_button = PushButton("格式化", self)
        self._format_button.setIcon(FluentIcon.CODE.icon())
        self._load_button = PushButton("打开文件", self)
        self._load_button.setIcon(resolve_fluent_icon("FOLDER"))
        self._clear_button = PushButton("清空", self)
        self._clear_button.setObjectName("dangerButton")
        self._clear_button.setIcon(FluentIcon.DELETE.icon())

        self._expand_button = PushButton("展开全部", self)
        self._expand_button.setIcon(FluentIcon.ZOOM_IN.icon())
        self._collapse_button = PushButton("折叠全部", self)
        self._collapse_button.setIcon(FluentIcon.ZOOM_OUT.icon())

        button_height = 42
        button_min_width = 138
        for btn in (
            self._parse_button,
            self._format_button,
            self._load_button,
            self._clear_button,
            self._copy_path_button,
            self._copy_value_button,
            self._expand_button,
            self._collapse_button,
        ):
            btn.setFixedHeight(button_height)
            btn.setMinimumWidth(button_min_width)

        path_bar = QHBoxLayout()
        path_bar.setSpacing(12)
        path_bar.setContentsMargins(0, 0, 0, 0)
        path_bar.addWidget(self._path_display, 1)
        path_bar.addWidget(self._copy_path_button)
        path_bar.addWidget(self._copy_value_button)

        button_bar = QHBoxLayout()
        button_bar.setSpacing(12)
        button_bar.setContentsMargins(0, 0, 0, 0)
        button_bar.addWidget(self._parse_button)
        button_bar.addWidget(self._format_button)
        button_bar.addWidget(self._load_button)
        button_bar.addWidget(self._clear_button)
        button_bar.addStretch(1)

        input_card = CardWidget(self)
        self._prepare_card(input_card)
        input_card.setObjectName("inputCard")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(24, 24, 24, 24)
        input_layout.setSpacing(18)
        title = BodyLabel("输入 JSON 数据", input_card)
        title.setObjectName("cardTitle")
        input_layout.addWidget(title)
        input_layout.addWidget(self._editor, 1)
        input_layout.addLayout(button_bar)

        output_card = CardWidget(self)
        self._prepare_card(output_card)
        output_card.setObjectName("outputCard")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(24, 24, 24, 24)
        output_layout.setSpacing(18)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)
        output_title = BodyLabel("解析结果", output_card)
        output_title.setObjectName("cardTitle")
        header_row.addWidget(output_title)
        header_row.addStretch(1)
        header_row.addWidget(self._filter_input, 2)
        header_row.addWidget(self._color_combo)
        header_row.addWidget(self._expand_button)
        header_row.addWidget(self._collapse_button)
        output_layout.addLayout(header_row)
        output_layout.addWidget(self._tree, 1)

        detail_card = CardWidget(self)
        self._prepare_card(detail_card)
        detail_card.setObjectName("detailCard")
        detail_layout = QVBoxLayout(detail_card)
        detail_layout.setContentsMargins(24, 24, 24, 24)
        detail_layout.setSpacing(18)

        detail_layout.addLayout(path_bar)
        detail_layout.addWidget(self._value_preview, 1)

        output_layout.addWidget(detail_card)

        self._apply_card_shadows(input_card, output_card, detail_card)

        self._button_icon_specs = [
            (self._parse_button, "PLAY", None, "primary"),
            (self._format_button, "CODE", None, "secondary"),
            (self._load_button, "FOLDER", "FOLDER_ADD", "secondary"),
            (self._clear_button, "DELETE", None, "danger"),
            (self._copy_path_button, "LINK", None, "primary"),
            (self._copy_value_button, "COPY", None, "secondary"),
            (self._expand_button, "ZOOM_IN", None, "secondary"),
            (self._collapse_button, "ZOOM_OUT", None, "secondary"),
        ]

        splitter = QSplitter(Qt.Horizontal, self)
        splitter.addWidget(input_card)
        splitter.addWidget(output_card)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 4)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(24)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        self._tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        self._tree.itemSelectionChanged.connect(self._on_tree_selection_change)
        self._filter_input.textChanged.connect(self._apply_filter)
        self._parse_button.clicked.connect(self.parse_json)
        self._format_button.clicked.connect(self.format_json)
        self._clear_button.clicked.connect(self.clear_all)
        self._load_button.clicked.connect(self._open_json_file)
        self._copy_path_button.clicked.connect(self._copy_selected_path)
        self._copy_value_button.clicked.connect(self._copy_selected_value)
        self._expand_button.clicked.connect(self._tree.expandAll)
        self._collapse_button.clicked.connect(self._tree.collapseAll)
        self._color_combo.currentTextChanged.connect(self.apply_color_scheme)

    # ------------------------------------------------------------------
    # Public operations
    # ------------------------------------------------------------------
    def parse_json(self) -> None:
        raw = self._editor.toPlainText().strip()
        if not raw:
            self._show_error("请输入 JSON 数据后再进行解析。")
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._show_error(f"JSON 解析失败: {exc.msg} (行 {exc.lineno}, 列 {exc.colno})")
            return

        self._populate_tree(data)

    def format_json(self) -> None:
        raw = self._editor.toPlainText().strip()
        if not raw:
            self._show_error("没有可以格式化的 JSON 内容。")
            return
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            self._show_error(f"JSON 无法格式化: {exc.msg} (行 {exc.lineno}, 列 {exc.colno})")
            return
        formatted = json.dumps(data, indent=4, ensure_ascii=False)
        self._editor.setPlainText(formatted)
        self._show_status("已格式化 JSON 文本。")

    def clear_all(self) -> None:
        self._editor.clear()
        self._tree.clear()
        self._filter_input.clear()
        self._path_display.clear()
        self._copy_path_button.setEnabled(False)
        self._copy_value_button.setEnabled(False)
        self._value_preview.setPlainText("选择节点以查看完整的 JSON 值…")
        self._show_status("已清空所有内容。")
        self.titleChanged.emit("新数据页")

    def set_text(self, text: str) -> None:
        self._editor.setPlainText(text)

    def apply_color_scheme(self, name: str) -> None:
        if name not in self.COLOR_SCHEMES:
            return
        self._current_scheme = name
        self._refresh_tree_colors()

    def apply_theme(self, theme: Theme) -> None:
        self._theme = theme
        self._editor.set_theme(theme)
        if theme == Theme.DARK:
            self._value_preview.setStyleSheet(
                "QPlainTextEdit#valuePreview {"
                " font-family: 'Cascadia Code', 'JetBrains Mono', monospace;"
                " font-size: 12px;"
                " border-radius: 10px;"
                " padding: 10px;"
                " background-color: #23252f;"
                " color: rgba(232, 236, 245, 225);"
                " selection-background-color: rgba(112, 134, 182, 200);"
                " selection-color: rgba(245, 248, 255, 235);"
                " border: 1px solid rgba(92, 102, 130, 180);"
                " }"
            )
            tree_bg = "#2a2d38"
            tree_alt_bg = "#313541"
            tree_border = "rgba(70, 78, 102, 150)"
            tree_text = "rgba(226, 230, 240, 220)"
            header_bg = "rgba(49, 53, 68, 220)"
            header_text = "rgba(223, 228, 240, 220)"
            header_border = "rgba(116, 132, 180, 140)"
            selection_bg = "rgba(88, 110, 150, 190)"
            selection_text = "rgba(244, 248, 255, 230)"
        else:
            self._value_preview.setStyleSheet(
                "QPlainTextEdit#valuePreview {"
                " font-family: 'Cascadia Code', 'JetBrains Mono', monospace;"
                " font-size: 12px;"
                " border-radius: 10px;"
                " padding: 10px;"
                " background-color: #ffffff;"
                " color: rgba(30, 33, 44, 210);"
                " selection-background-color: rgba(135, 169, 255, 120);"
                " selection-color: rgba(24, 32, 45, 220);"
                " border: 1px solid rgba(200, 210, 230, 150);"
                " }"
            )
            tree_bg = "#ffffff"
            tree_alt_bg = "#f5f8ff"
            tree_border = "rgba(185, 195, 215, 110)"
            tree_text = "rgba(44, 48, 60, 220)"
            header_bg = "rgba(242, 245, 252, 230)"
            header_text = "rgba(70, 78, 100, 220)"
            header_border = "rgba(176, 188, 224, 150)"
            selection_bg = "rgba(135, 169, 255, 120)"
            selection_text = "rgba(24, 32, 45, 220)"

        self._tree.setStyleSheet(
            f"""
            QTreeWidget {{
                background-color: {tree_bg};
                alternate-background-color: {tree_alt_bg};
                border: 1px solid {tree_border};
                border-radius: 14px;
                color: {tree_text};
                padding: 6px;
            }}
            QTreeWidget::item {{
                height: 30px;
                margin: 2px 0px;
                padding: 4px 8px;
                border-radius: 8px;
            }}
            QTreeWidget::item:selected {{
                background-color: {selection_bg};
                color: {selection_text};
            }}
            QHeaderView::section {{
                background-color: {header_bg};
                color: {header_text};
                border: none;
                border-bottom: 1px solid {header_border};
                padding: 6px 12px;
                font-weight: 500;
                font-size: 13px;
                letter-spacing: 0.2px;
            }}
            QHeaderView::section:horizontal {{
                margin: 0px;
            }}
            """
        )
        self._refresh_tree_colors()
        self._apply_button_palette()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _open_json_file(self) -> None:
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
        self._editor.setPlainText(content)
        self._show_status(f"已加载文件：{file_path.name}")
        self.titleChanged.emit(file_path.name)

    def _populate_tree(self, data: Any) -> None:
        self._tree.clear()
        self._path_display.clear()
        self._copy_path_button.setEnabled(False)
        self._copy_value_button.setEnabled(False)
        self._value_preview.setPlainText("选择节点以查看完整的 JSON 值…")

        if isinstance(data, dict):
            for key, value in data.items():
                item = self._create_tree_item(key, value, key)
                if item is not None:
                    self._tree.addTopLevelItem(item)
        elif isinstance(data, list):
            for index, value in enumerate(data):
                path = f"[{index}]"
                item = self._create_tree_item(f"[{index}]", value, path)
                if item is not None:
                    self._tree.addTopLevelItem(item)
        else:
            item = self._create_tree_item("值", data, "值")
            if item is not None:
                self._tree.addTopLevelItem(item)

        self._tree.expandToDepth(1)
        keyword = self._filter_input.text().strip()
        if keyword:
            self._apply_filter(keyword)
        else:
            self._reset_filter()
        self._show_status(self._summarize_data(data))
        self._refresh_tree_colors()

    def _create_tree_item(self, key: str, value: Any, path: str) -> Optional[QTreeWidgetItem]:
        type_name: str
        if isinstance(value, dict):
            item = QTreeWidgetItem([str(key), self._describe_value(value)])
            type_name = "object"
            for child_key, child_value in value.items():
                child_path = f"{path}.{child_key}" if path else child_key
                child_item = self._create_tree_item(child_key, child_value, child_path)
                if child_item is not None:
                    item.addChild(child_item)
        elif isinstance(value, list):
            item = QTreeWidgetItem([str(key), self._describe_value(value)])
            type_name = "array"
            for index, child_value in enumerate(value):
                child_path = f"{path}[{index}]" if path else f"[{index}]"
                child_item = self._create_tree_item(f"[{index}]", child_value, child_path)
                if child_item is not None:
                    item.addChild(child_item)
        else:
            text = self._format_scalar(value)
            item = QTreeWidgetItem([str(key), text])
            type_name = self._detect_scalar_type(value)
        item.setData(0, Qt.UserRole, path)
        item.setData(0, Qt.UserRole + 1, value)
        item.setData(0, Qt.UserRole + 2, type_name)
        return item

    def _describe_value(self, value: Any) -> str:
        if isinstance(value, dict):
            return f"对象（{len(value)} 项）"
        if isinstance(value, list):
            return f"数组（{len(value)} 项）"
        return self._format_scalar(value)

    def _format_scalar(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(value, ensure_ascii=False)

    def _detect_scalar_type(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, (int, float)):
            return "number"
        return "string"

    def _show_tree_context_menu(self, position: QPoint) -> None:
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
        items = self._tree.selectedItems()
        if not items:
            self._path_display.clear()
            self._copy_path_button.setEnabled(False)
            self._copy_value_button.setEnabled(False)
            self._value_preview.setPlainText("选择节点以查看完整的 JSON 值…")
            return
        item = items[0]
        path = item.data(0, Qt.UserRole) or ""
        value = item.data(0, Qt.UserRole + 1)
        if isinstance(value, (dict, list)):
            pretty_value = json.dumps(value, indent=4, ensure_ascii=False)
        else:
            pretty_value = self._format_scalar(value)
        self._path_display.setText(path)
        self._copy_path_button.setEnabled(True)
        self._copy_value_button.setEnabled(True)
        self._value_preview.setPlainText(pretty_value)

    def _copy_selected_path(self) -> None:
        text = self._path_display.text().strip()
        if not text:
            return
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        self._show_status("JSON 路径已复制到剪贴板。", 1600)

    def _copy_selected_value(self) -> None:
        items = self._tree.selectedItems()
        if not items:
            return
        value = items[0].data(0, Qt.UserRole + 1)
        if isinstance(value, (dict, list)):
            text = json.dumps(value, ensure_ascii=False)
        else:
            text = self._format_scalar(value)
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(text)
        self._show_status("节点值已复制到剪贴板。", 1600)

    def _apply_filter(self, keyword: str) -> None:
        keyword = keyword.strip()
        if not keyword:
            self._reset_filter()
            return

        self._tree.setUpdatesEnabled(False)
        total_match = 0

        def _filter(item: QTreeWidgetItem) -> bool:
            nonlocal total_match
            match = keyword.lower() in item.text(0).lower() or keyword.lower() in item.text(1).lower()
            child_match = False
            for idx in range(item.childCount()):
                if _filter(item.child(idx)):
                    child_match = True
            visible = match or child_match
            item.setHidden(not visible)
            if visible:
                total_match += 1
            if item.childCount() and visible:
                item.setExpanded(True)
            return visible

        for index in range(self._tree.topLevelItemCount()):
            _filter(self._tree.topLevelItem(index))

        self._tree.setUpdatesEnabled(True)
        self._show_status(f"已找到 {total_match} 个匹配节点。")

    def _reset_filter(self) -> None:
        self._tree.setUpdatesEnabled(False)
        for index in range(self._tree.topLevelItemCount()):
            self._show_item_recursive(self._tree.topLevelItem(index))
        self._tree.setUpdatesEnabled(True)
        visible = self._count_visible_items()
        self._show_status(f"当前可见节点 {visible} 个。")

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

    def _refresh_tree_colors(self) -> None:
        scheme = self.COLOR_SCHEMES.get(self._current_scheme)
        if not scheme:
            return
        palette = scheme["dark" if self._theme == Theme.DARK else "light"]

        def _apply(item: QTreeWidgetItem) -> None:
            type_name = item.data(0, Qt.UserRole + 2)
            base_color = palette.get(type_name, palette.get("default", QColor("#444")))
            key_color = QColor(base_color)
            value_color = QColor(base_color)
            if self._theme == Theme.DARK:
                key_color.setAlpha(240)
                value_color = QColor(base_color).lighter(120)
                value_color.setAlpha(235)
            else:
                key_color.setAlpha(255)
                value_color.setAlpha(240)
            item.setForeground(0, QBrush(key_color))
            item.setForeground(1, QBrush(value_color))
            for idx in range(item.childCount()):
                _apply(item.child(idx))

        for index in range(self._tree.topLevelItemCount()):
            _apply(self._tree.topLevelItem(index))

    def _summarize_data(self, data: Any) -> str:
        if isinstance(data, dict):
            return f"解析成功：根对象包含 {len(data)} 个键。"
        if isinstance(data, list):
            return f"解析成功：根数组包含 {len(data)} 个元素。"
        return "解析成功：根节点为原始值。"

    def _show_error(self, message: str) -> None:
        QMessageBox.critical(self, "错误", message)
        self._show_status("发生错误：" + message, 3500)

    def _show_status(self, message: str, timeout: int = 3500) -> None:
        window = self.window()
        if window is None:
            return
        callback = getattr(window, "show_status_message", None)
        if callable(callback):
            callback(message, timeout)

    def _apply_card_shadows(self, *cards: CardWidget) -> None:
        for card in cards:
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(28)
            shadow.setXOffset(0)
            shadow.setYOffset(12)
            shadow.setColor(QColor(20, 20, 20, 35))
            card.setGraphicsEffect(shadow)

    def _prepare_card(self, card: CardWidget) -> None:
        card.setAttribute(Qt.WA_StyledBackground, True)
        card.setAttribute(Qt.WA_TranslucentBackground, True)
        card.setAutoFillBackground(False)

    def _apply_button_palette(self) -> None:
        if not hasattr(self, "_button_icon_specs"):
            return

        if self._theme == Theme.DARK:
            primary_icon = QColor(244, 247, 255)
            secondary_icon = QColor(208, 214, 235)
            danger_icon = QColor(255, 172, 172)
        else:
            primary_icon = QColor(255, 255, 255)
            secondary_icon = QColor(76, 101, 148)
            danger_icon = QColor(234, 85, 85)

        for button, name, fallback, role in self._button_icon_specs:
            if role == "primary":
                icon_color = primary_icon
            elif role == "danger":
                icon_color = danger_icon
            else:
                icon_color = secondary_icon
            button.setIcon(resolve_fluent_icon(name, fallback or name, icon_color))


class JsonParserWindow(QMainWindow):
    """Main window hosting multiple JSON workspaces."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("JSON 数据洞察工具")
        self.resize(1280, 780)

        self._current_theme = Theme.LIGHT
        setTheme(self._current_theme)
        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

        self._hero_card = GradientHeroCard(self)
        self._controls_card = CardWidget(self)
        self._theme_combo = ComboBox(self)
        self._new_tab_button = PrimaryPushButton("新建数据页", self)
        self._new_tab_button.setIcon(FluentIcon.ADD.icon())
        self._new_tab_button.setFixedHeight(42)
        self._new_tab_button.setMinimumWidth(138)

        self._tab_widget = QTabWidget(self)
        self._tab_widget.setDocumentMode(True)
        self._tab_widget.setTabsClosable(False)
        self._tab_widget.setMovable(True)
        self._tab_bar = WorkspaceTabBar(self._tab_widget)
        self._tab_bar.tabCloseRequested.connect(self._close_tab)
        self._tab_widget.setTabBar(self._tab_bar)
        self._tab_widget.currentChanged.connect(self._on_tab_changed)

        self._build_ui()
        self._apply_global_styles(self._current_theme)
        self._add_workspace("数据页 1")
        self.show_status_message("准备就绪。", 2000)

    # ------------------------------------------------------------------
    # UI assembly
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        hero_layout = QVBoxLayout(self._hero_card)
        hero_layout.setContentsMargins(24, 22, 24, 22)
        hero_layout.setSpacing(10)
        title = BodyLabel("JSON 数据洞察工具", self._hero_card)
        title.setObjectName("heroTitle")
        subtitle = CaptionLabel(
            "Fluent Design 风格的专业解析器，支持多标签、多配色、复制路径与值。",
            self._hero_card,
        )
        subtitle.setObjectName("heroSubtitle")
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        hero_layout.addStretch(1)
        signature = CaptionLabel("By:ChatGPT Code & BigTiger", self._hero_card)
        signature.setObjectName("heroSignature")
        hero_layout.addWidget(signature, 0, Qt.AlignRight | Qt.AlignBottom)

        controls_card = self._controls_card
        controls_card.setParent(self)
        controls_card.setAttribute(Qt.WA_StyledBackground, True)
        controls_card.setAttribute(Qt.WA_TranslucentBackground, True)
        controls_card.setAutoFillBackground(False)
        controls_card.setObjectName("controlsCard")
        controls_layout = QHBoxLayout(controls_card)
        controls_layout.setContentsMargins(24, 16, 24, 16)
        controls_layout.setSpacing(18)

        theme_label = CaptionLabel("主题模式", controls_card)
        self._theme_combo.addItem("浅色模式")
        self._theme_combo.addItem("深色模式")
        self._theme_combo.setCurrentIndex(0)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)

        controls_layout.addWidget(theme_label)
        controls_layout.addWidget(self._theme_combo)
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._new_tab_button)
        self._new_tab_button.clicked.connect(self._create_new_tab)

        central = QWidget(self)
        central.setObjectName("centralWidget")
        layout = QVBoxLayout(central)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(20)
        layout.addWidget(self._hero_card)
        layout.addWidget(self._controls_card)
        layout.addWidget(self._tab_widget, 1)
        self.setCentralWidget(central)
        self._apply_card_shadows(self._hero_card, self._controls_card)

    def show_status_message(self, message: str, timeout: int = 3500) -> None:
        self._status_bar.showMessage(message, timeout)

    # ------------------------------------------------------------------
    # Workspace helpers
    # ------------------------------------------------------------------
    def _apply_card_shadows(self, *cards: CardWidget) -> None:
        for card in cards:
            shadow = QGraphicsDropShadowEffect(card)
            shadow.setBlurRadius(28)
            shadow.setXOffset(0)
            shadow.setYOffset(12)
            shadow.setColor(QColor(20, 20, 20, 35))
            card.setGraphicsEffect(shadow)

    def _create_new_tab(self) -> None:
        count = self._tab_widget.count() + 1
        title = f"数据页 {count}"
        self._add_workspace(title)
        self._tab_widget.setCurrentIndex(self._tab_widget.count() - 1)

    def _add_workspace(self, title: str) -> None:
        workspace = JsonWorkspace(self)
        workspace.apply_theme(self._current_theme)
        index = self._tab_widget.addTab(workspace, title)
        workspace.titleChanged.connect(lambda name, ws=workspace: self._update_tab_title_from_workspace(ws, name))
        self._tab_widget.setCurrentIndex(index)

    def _update_tab_title_from_workspace(self, workspace: JsonWorkspace, title: str) -> None:
        index = self._tab_widget.indexOf(workspace)
        if index == -1:
            return
        if not title:
            title = f"数据页 {index + 1}"
        self._tab_widget.setTabText(index, title)

    def _close_tab(self, index: int) -> None:
        if self._tab_widget.count() == 1:
            workspace: JsonWorkspace = self._tab_widget.widget(index)
            workspace.clear_all()
            return
        widget = self._tab_widget.widget(index)
        widget.deleteLater()
        self._tab_widget.removeTab(index)

    def _on_tab_changed(self, index: int) -> None:
        if index < 0:
            return
        workspace: JsonWorkspace = self._tab_widget.widget(index)
        workspace.apply_theme(self._current_theme)

    def _on_theme_changed(self, index: int) -> None:
        theme = Theme.LIGHT if index == 0 else Theme.DARK
        if theme == self._current_theme:
            return
        self._current_theme = theme
        setTheme(theme)
        self._apply_global_styles(theme)
        for tab in range(self._tab_widget.count()):
            workspace: JsonWorkspace = self._tab_widget.widget(tab)
            workspace.apply_theme(theme)

    def _apply_global_styles(self, theme: Theme) -> None:
        if theme == Theme.DARK:
            palette = {
                "central_bg": "#1d2029",
                "card_bg": "#272c3b",
                "detail_bg": "#202431",
                "text_color": "rgba(226, 231, 245, 220)",
                "line_edit_bg": "#242837",
                "line_edit_fg": "rgba(228, 232, 245, 220)",
                "line_edit_border": "rgba(86, 98, 132, 200)",
                "card_border": "rgba(64, 74, 104, 190)",
                "detail_border": "rgba(88, 100, 138, 190)",
                "combo_bg": "#292e3d",
                "combo_fg": "rgba(224, 229, 242, 220)",
                "combo_border": "rgba(92, 104, 140, 180)",
                "splitter_color": "rgba(118, 132, 170, 130)",
                "status_bg": "#1f232e",
                "status_fg": "rgba(222, 227, 238, 220)",
                "status_border": "rgba(72, 82, 116, 170)",
                "primary_bg": "#4274ff",
                "primary_bg_hover": "#5a86ff",
                "primary_bg_press": "#335edc",
                "primary_fg": "#f4f7ff",
                "secondary_bg": "#30364a",
                "secondary_bg_hover": "#3b4156",
                "secondary_bg_press": "#2a3042",
                "secondary_fg": "rgba(222, 228, 241, 220)",
                "secondary_border": "rgba(115, 130, 170, 180)",
                "secondary_border_hover": "rgba(138, 152, 192, 210)",
                "danger_bg": "#d56767",
                "danger_hover": "#df7777",
                "danger_press": "#bf5656",
                "danger_border": "#e88f8f",
                "danger_fg": "#fff6f6",
                "tab_active_bg": "#353a4d",
                "tab_active_border": "rgba(108, 128, 180, 200)",
                "tab_active_fg": "#f3f6ff",
                "tab_inactive_fg": "rgba(166, 178, 210, 210)",
                "tab_hover_bg": "#2d3144",
                "scrollbar_handle_idle": "rgba(0, 0, 0, 0)",
                "scrollbar_handle_hover": "rgba(138, 154, 210, 0.85)",
                "scrollbar_handle_pressed": "rgba(120, 138, 200, 0.95)",
                "scrollbar_track_hover": "rgba(76, 90, 128, 0.35)",
                "scrollbar_track_active": "rgba(76, 90, 128, 0.45)",
                "hero_signature": "rgba(255, 255, 255, 230)",
            }
        else:
            palette = {
                "central_bg": "#f2f4fb",
                "card_bg": "#ffffff",
                "detail_bg": "#f8f9fe",
                "text_color": "rgba(38, 46, 66, 220)",
                "line_edit_bg": "#ffffff",
                "line_edit_fg": "rgba(40, 48, 68, 220)",
                "line_edit_border": "rgba(168, 178, 204, 140)",
                "card_border": "rgba(206, 214, 234, 160)",
                "detail_border": "rgba(188, 198, 220, 150)",
                "combo_bg": "#ffffff",
                "combo_fg": "rgba(40, 48, 68, 220)",
                "combo_border": "rgba(172, 182, 210, 150)",
                "splitter_color": "rgba(132, 148, 200, 140)",
                "status_bg": "#ffffff",
                "status_fg": "rgba(40, 48, 68, 220)",
                "status_border": "rgba(206, 214, 234, 160)",
                "primary_bg": "#3f6bff",
                "primary_bg_hover": "#517bff",
                "primary_bg_press": "#3258e0",
                "primary_fg": "#ffffff",
                "secondary_bg": "#eef1ff",
                "secondary_bg_hover": "#e4e8ff",
                "secondary_bg_press": "#d8defe",
                "secondary_fg": "rgba(55, 66, 98, 220)",
                "secondary_border": "rgba(168, 182, 220, 180)",
                "secondary_border_hover": "rgba(146, 162, 212, 210)",
                "danger_bg": "#ef6666",
                "danger_hover": "#f07a7a",
                "danger_press": "#d85c5c",
                "danger_border": "#f4a2a2",
                "danger_fg": "#fff7f7",
                "tab_active_bg": "#ffffff",
                "tab_active_border": "rgba(198, 206, 232, 170)",
                "tab_active_fg": "rgba(40, 48, 68, 220)",
                "tab_inactive_fg": "rgba(120, 134, 168, 210)",
                "tab_hover_bg": "#e5ebff",
                "scrollbar_handle_idle": "rgba(0, 0, 0, 0)",
                "scrollbar_handle_hover": "rgba(120, 150, 230, 0.75)",
                "scrollbar_handle_pressed": "rgba(104, 132, 210, 0.9)",
                "scrollbar_track_hover": "rgba(160, 178, 228, 0.35)",
                "scrollbar_track_active": "rgba(160, 178, 228, 0.45)",
                "hero_signature": "rgba(255, 255, 255, 230)",
            }

        stylesheet_template = Template(
            """
            #centralWidget {
                background: ${central_bg};
            }
            CardWidget#heroCard {
                border-radius: 22px;
                background-color: transparent;
                color: white;
            }
            BodyLabel#heroTitle { font-size: 28px; font-weight: 600; }
            CaptionLabel#heroSubtitle { font-size: 14px; color: rgba(255, 255, 255, 210); }
            CaptionLabel#heroSignature { font-size: 18px; font-weight: 500; letter-spacing: 0.6px; color: ${hero_signature}; margin-top: 4px; }
            CardWidget#controlsCard {
                border-radius: 18px;
                background-color: ${card_bg};
                border: 1px solid ${card_border};
            }
            CardWidget#inputCard, CardWidget#outputCard {
                border-radius: 20px;
                background-color: ${card_bg};
                border: 1px solid ${card_border};
                padding: 6px;
            }
            CardWidget#detailCard {
                border-radius: 18px;
                background-color: ${detail_bg};
                border: 1px solid ${detail_border};
            }
            QWidget#workspacePage {
                background-color: transparent;
            }
            LineEdit {
                border-radius: 10px;
                padding: 6px 12px;
                font-size: 13px;
                background-color: ${line_edit_bg};
                color: ${line_edit_fg};
                border: 1px solid ${line_edit_border};
            }
            LineEdit#filterBox { min-width: 240px; }
            ComboBox {
                min-width: 150px;
                background-color: ${combo_bg};
                color: ${combo_fg};
                border-radius: 10px;
                border: 1px solid ${combo_border};
                padding: 4px 12px;
            }
            BodyLabel#cardTitle { font-size: 14px; font-weight: 400; color: ${text_color}; }
            PrimaryPushButton {
                border-radius: 18px;
                padding: 6px 24px;
                background-color: ${primary_bg};
                color: ${primary_fg};
                border: none;
                min-height: 42px;
            }
            PrimaryPushButton:hover {
                background-color: ${primary_bg_hover};
            }
            PrimaryPushButton:pressed {
                background-color: ${primary_bg_press};
            }
            PrimaryPushButton:disabled {
                background-color: rgba(120, 130, 160, 90);
                color: rgba(255, 255, 255, 120);
            }
            PushButton {
                border-radius: 18px;
                padding: 6px 24px;
                background-color: ${secondary_bg};
                color: ${secondary_fg};
                border: 1px solid ${secondary_border};
                min-height: 42px;
            }
            PushButton:hover {
                background-color: ${secondary_bg_hover};
                border: 1px solid ${secondary_border_hover};
            }
            PushButton:pressed {
                background-color: ${secondary_bg_press};
            }
            PushButton:disabled {
                background-color: rgba(120, 130, 160, 60);
                color: rgba(210, 215, 230, 110);
                border: 1px solid rgba(150, 160, 185, 70);
            }
            PushButton#dangerButton {
                background-color: ${danger_bg};
                color: ${danger_fg};
                border: 1px solid ${danger_border};
            }
            PushButton#dangerButton:hover {
                background-color: ${danger_hover};
                border-color: ${danger_border};
            }
            PushButton#dangerButton:pressed {
                background-color: ${danger_press};
            }
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabWidget::tab-bar {
                alignment: left;
                margin: 8px 20px 4px 20px;
            }
            QTabBar {
                qproperty-drawBase: 0;
                background: transparent;
            }
            QTabBar::tab {
                border-radius: 16px;
                padding: 10px 28px;
                margin: 4px 8px;
                min-width: 280px;
                color: ${tab_inactive_fg};
                background-color: transparent;
            }
            QTabBar::tab:selected {
                background-color: ${tab_active_bg};
                color: ${tab_active_fg};
                border: 1px solid ${tab_active_border};
                font-weight: 500;
            }
            QTabBar::tab:!selected {
                background-color: transparent;
            }
            QTabBar::tab:hover {
                background-color: ${tab_hover_bg};
            }
            QSplitter {
                padding: 0px;
            }
            QSplitter::handle {
                background-color: transparent;
                width: 24px;
                margin: 0px 12px;
            }
            QSplitter::handle:horizontal:hover,
            QSplitter::handle:horizontal:pressed {
                background-color: ${splitter_color};
                border-radius: 12px;
            }
            QStatusBar {
                background-color: ${status_bg};
                color: ${status_fg};
                border-top: 1px solid ${status_border};
                padding: 4px 12px;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
                margin: 4px 4px 4px 0px;
            }
            QScrollBar::handle:vertical {
                background-color: ${scrollbar_handle_idle};
                border-radius: 5px;
                min-height: 28px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: ${scrollbar_handle_hover};
            }
            QScrollBar::handle:vertical:pressed {
                background-color: ${scrollbar_handle_pressed};
            }
            QScrollBar:vertical:hover {
                background-color: ${scrollbar_track_hover};
                border-radius: 6px;
            }
            QScrollBar:vertical:pressed {
                background-color: ${scrollbar_track_active};
                border-radius: 6px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 10px;
                margin: 0px 4px 4px 4px;
            }
            QScrollBar::handle:horizontal {
                background-color: ${scrollbar_handle_idle};
                border-radius: 5px;
                min-width: 28px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: ${scrollbar_handle_hover};
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: ${scrollbar_handle_pressed};
            }
            QScrollBar:horizontal:hover {
                background-color: ${scrollbar_track_hover};
                border-radius: 6px;
            }
            QScrollBar:horizontal:pressed {
                background-color: ${scrollbar_track_active};
                border-radius: 6px;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            """
        )
        stylesheet = stylesheet_template.substitute(palette)
        self.setStyleSheet(stylesheet)
        self._hero_card.set_theme(theme)
        new_tab_icon_color = QColor(255, 255, 255) if theme == Theme.LIGHT else QColor(244, 247, 255)
        self._new_tab_button.setIcon(resolve_fluent_icon("ADD", color=new_tab_icon_color))
        self._tab_bar.set_theme(theme)


def main() -> None:
    import sys

    app = QApplication(sys.argv)
    window = JsonParserWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
