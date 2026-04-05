from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData, QSettings, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QKeySequence,
    QShortcut,
    QTextCharFormat,
    QTextCursor,
    QWheelEvent,
)
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import RepairMode, ThemeMode, UiLanguage, UiMessage
from .localization import render_ui_message, render_ui_warning, translate
from .search_bar import InlineSearchBar
from .theme import ThemeSpec, get_theme, qcolor

REPAIR_MODE_KEY = "ui/repair_mode"
LAST_OPEN_PATH_KEY = "ui/last_open_path"


class ZoomableTextEdit(QTextEdit):
    fontZoomRequested = Signal(int)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.modifiers() & Qt.ControlModifier:
            angle_delta = event.angleDelta().y()
            if angle_delta:
                self.fontZoomRequested.emit(1 if angle_delta > 0 else -1)
                event.accept()
                return

        super().wheelEvent(event)


class InputPanel(QWidget):
    openFileRequested = Signal(str)
    fileDropped = Signal(str)
    repairModeChanged = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._settings = self._create_settings()
        self._last_open_path = self._load_last_open_path()
        self._language: UiLanguage = "ko"
        self._theme_mode: ThemeMode = "system"
        self._theme: ThemeSpec = get_theme("system")
        self._error_line: int | None = None
        self._error_column: int | None = None
        self._error_index: int | None = None
        self._summary_messages: list[UiMessage] = []
        self._warning_messages: list[UiMessage] = []
        self._risk_level: str | None = None
        self._diff_spans: list[tuple[int, int]] = []
        self._diff_highlight_enabled = True
        self._search_matches: list[tuple[int, int]] = []
        self._active_search_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.title_label = QLabel(header)
        self.open_button = QPushButton(header)
        self.search_button = QPushButton(header)
        self.mode_label = QLabel(header)
        self.mode_combo = QComboBox(header)

        self.mode_combo.addItem("", "strict")
        self.mode_combo.addItem("", "safe")
        self.mode_combo.addItem("", "aggressive")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.open_button)
        header_layout.addWidget(self.search_button)
        header_layout.addWidget(self.mode_label)
        header_layout.addWidget(self.mode_combo)

        self.search_bar = InlineSearchBar(self)

        self.input_edit = ZoomableTextEdit(self)
        self.input_edit.setAcceptRichText(False)
        self.open_shortcut = QShortcut(QKeySequence.Open, self)

        metadata_header = QHBoxLayout()
        metadata_header.setContentsMargins(0, 0, 0, 0)
        metadata_header.setSpacing(8)
        self.summary_label = QLabel(self)
        self.risk_badge = QLabel("", self)
        self.risk_badge.setVisible(False)
        metadata_header.addWidget(self.summary_label)
        metadata_header.addStretch(1)
        metadata_header.addWidget(self.risk_badge)

        self.summary_edit = QTextEdit(self)
        self.summary_edit.setReadOnly(True)
        self.summary_edit.setMaximumHeight(90)

        self.warning_label = QLabel(self)
        self.warning_edit = QTextEdit(self)
        self.warning_edit.setReadOnly(True)
        self.warning_edit.setMaximumHeight(90)

        layout.addWidget(header)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.input_edit, 1)
        layout.addLayout(metadata_header)
        layout.addWidget(self.summary_edit)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.warning_edit)

        self._restore_repair_mode()
        self._wire_actions()
        self.apply_language("ko")
        self.apply_theme(self._theme)
        self.clear_error_highlight()
        self._reset_summary_widgets()

    def _create_settings(self) -> QSettings:
        return QSettings()

    def _wire_actions(self) -> None:
        self.open_button.clicked.connect(self._emit_open_file_requested)
        self.search_button.clicked.connect(self.show_search)
        self.open_shortcut.activated.connect(self._emit_open_file_requested)
        self.mode_combo.currentIndexChanged.connect(self._handle_mode_changed)
        self.search_bar.query_edit.textChanged.connect(self._handle_search_text_changed)
        self.search_bar.nextRequested.connect(lambda: self._move_search(1))
        self.search_bar.previousRequested.connect(lambda: self._move_search(-1))
        self.search_bar.closed.connect(self._handle_search_closed)
        self.input_edit.textChanged.connect(self._handle_text_changed)

    def _load_last_open_path(self) -> str:
        raw_value = self._settings.value(LAST_OPEN_PATH_KEY, "")
        return raw_value if isinstance(raw_value, str) else ""

    def _restore_repair_mode(self) -> None:
        stored_mode = str(self._settings.value(REPAIR_MODE_KEY, "safe"))
        index = self.mode_combo.findData(stored_mode)
        if index < 0:
            index = self.mode_combo.findData("safe")
        self.mode_combo.setCurrentIndex(index)

    def apply_language(self, language: UiLanguage) -> None:
        self._language = language
        self.title_label.setText(translate(language, "label.input_title"))
        self.open_button.setText(translate(language, "button.open_file"))
        self.search_button.setText(translate(language, "button.search"))
        self.mode_label.setText(translate(language, "label.repair_mode"))
        self.input_edit.setPlaceholderText(translate(language, "placeholder.input"))
        self.summary_label.setText(translate(language, "label.summary"))
        self.warning_label.setText(translate(language, "label.warnings"))
        self.summary_edit.setPlaceholderText(translate(language, "placeholder.summary"))
        self.warning_edit.setPlaceholderText(translate(language, "placeholder.warnings"))
        self.search_bar.apply_language(language)
        self._set_mode_item_labels()
        self._render_summary()

    def apply_theme(self, theme: ThemeSpec) -> None:
        self._theme = theme
        self.setStyleSheet(
            "\n".join(
                [
                    f"QWidget {{ color: {theme.foreground}; }}",
                    (
                        "QPushButton, QComboBox {"
                        f" background: {theme.surface_background};"
                        f" color: {theme.foreground};"
                        f" border: 1px solid {theme.border};"
                        " padding: 4px 8px; }"
                    ),
                    (
                        "QLabel {"
                        f" color: {theme.foreground};"
                        " }"
                    ),
                ]
            )
        )
        self.input_edit.setStyleSheet(
            (
                "QTextEdit {"
                f" background: {theme.input_background};"
                f" color: {theme.foreground};"
                f" border: 1px solid {theme.border};"
                f" selection-background-color: {theme.selection_background};"
                f" selection-color: {theme.selection_foreground};"
                " }"
            )
        )
        self.summary_edit.setStyleSheet(
            (
                "QTextEdit {"
                f" background: {theme.surface_alt_background};"
                f" color: {theme.foreground};"
                f" border: 1px solid {theme.border};"
                " }"
            )
        )
        self.warning_edit.setStyleSheet(
            (
                "QTextEdit {"
                f" background: {theme.warning_background};"
                f" color: {theme.warning_foreground};"
                f" border: 1px solid {theme.border};"
                " }"
            )
        )
        self.search_bar.apply_theme(theme)
        self._set_risk_badge(self._risk_level)
        self._refresh_highlights()

    def apply_editor_font(self, font: QFont) -> None:
        self.input_edit.setFont(font)

    def set_text(self, text: str) -> None:
        self.input_edit.setPlainText(text)

    def get_text(self) -> str:
        return self.input_edit.toPlainText()

    def current_repair_mode(self) -> RepairMode:
        mode = self.mode_combo.currentData()
        if isinstance(mode, str) and mode in {"strict", "safe", "aggressive"}:
            return mode
        return "safe"

    def set_repair_mode(self, mode: RepairMode) -> None:
        index = self.mode_combo.findData(mode)
        if index >= 0:
            self.mode_combo.setCurrentIndex(index)

    def last_open_path(self) -> str:
        return self._last_open_path

    def set_last_open_path(self, path: str) -> None:
        if not path:
            return
        self._last_open_path = path
        self._settings.setValue(LAST_OPEN_PATH_KEY, path)
        self._settings.sync()

    def show_search(self) -> None:
        self.search_bar.open_bar()

    def clear_error_highlight(self) -> None:
        self._error_line = None
        self._error_column = None
        self._error_index = None
        self._refresh_highlights()

    def highlight_error(
        self,
        *,
        line: int | None = None,
        column: int | None = None,
        index: int | None = None,
    ) -> None:
        self._error_line = line
        self._error_column = column
        self._error_index = index
        self._focus_error_location()
        self._refresh_highlights()

    def set_diff_spans(self, spans: list[tuple[int, int]]) -> None:
        self._diff_spans = spans
        self._refresh_highlights()

    def clear_diff_spans(self) -> None:
        self._diff_spans = []
        self._refresh_highlights()

    def set_diff_highlight_enabled(self, enabled: bool) -> None:
        self._diff_highlight_enabled = enabled
        self._refresh_highlights()

    def set_summary(
        self,
        change_summary: list[UiMessage],
        repair_warnings: list[UiMessage],
        risk_level: str | None,
    ) -> None:
        self._summary_messages = change_summary
        self._warning_messages = repair_warnings
        self._risk_level = risk_level
        self._render_summary()

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        if self._first_local_file_path(event.mimeData()) is not None:
            event.acceptProposedAction()
            return
        event.ignore()

    def dropEvent(self, event) -> None:  # type: ignore[override]
        path = self._first_local_file_path(event.mimeData())
        if path is None:
            event.ignore()
            return

        self.set_last_open_path(path)
        self.fileDropped.emit(path)
        event.acceptProposedAction()

    def _set_mode_item_labels(self) -> None:
        current_mode = self.current_repair_mode()
        labels = [
            ("strict", translate(self._language, "combo.mode.strict")),
            ("safe", translate(self._language, "combo.mode.safe")),
            ("aggressive", translate(self._language, "combo.mode.aggressive")),
        ]
        self.mode_combo.blockSignals(True)
        self.mode_combo.clear()
        for data, label in labels:
            self.mode_combo.addItem(label, data)
        self.mode_combo.setCurrentIndex(max(0, self.mode_combo.findData(current_mode)))
        self.mode_combo.blockSignals(False)

    def _handle_mode_changed(self, _index: int) -> None:
        mode = self.current_repair_mode()
        self._settings.setValue(REPAIR_MODE_KEY, mode)
        self._settings.sync()
        self.repairModeChanged.emit(mode)

    def _emit_open_file_requested(self) -> None:
        self.openFileRequested.emit(self.last_open_path())

    def _first_local_file_path(self, mime_data: QMimeData) -> str | None:
        for url in mime_data.urls():
            if url.isLocalFile():
                return str(Path(url.toLocalFile()))
        return None

    def _handle_text_changed(self) -> None:
        if self.search_bar.isHidden():
            return
        self._recompute_search_matches(self.search_bar.query_edit.text())

    def _handle_search_text_changed(self, text: str) -> None:
        self._recompute_search_matches(text)

    def _handle_search_closed(self) -> None:
        self.search_bar.query_edit.blockSignals(True)
        self.search_bar.query_edit.clear()
        self.search_bar.query_edit.blockSignals(False)
        self._search_matches = []
        self._active_search_index = -1
        self._refresh_highlights()

    def _recompute_search_matches(self, term: str) -> None:
        self._search_matches = _find_text_matches(self.get_text(), term)
        self._active_search_index = 0 if self._search_matches else -1
        self.search_bar.set_result_state(len(self._search_matches), self._active_search_index + 1 if self._search_matches else 0)
        self._focus_active_search()
        self._refresh_highlights()

    def _move_search(self, direction: int) -> None:
        if not self._search_matches:
            return
        self._active_search_index = (self._active_search_index + direction) % len(self._search_matches)
        self.search_bar.set_result_state(len(self._search_matches), self._active_search_index + 1)
        self._focus_active_search()
        self._refresh_highlights()

    def _focus_active_search(self) -> None:
        if self._active_search_index < 0 or not self._search_matches:
            return
        start, end = self._search_matches[self._active_search_index]
        cursor = self.input_edit.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.input_edit.setTextCursor(cursor)
        self.input_edit.ensureCursorVisible()

    def _focus_error_location(self) -> None:
        cursor = self._cursor_for_error()
        if cursor is None:
            return
        self.input_edit.setTextCursor(cursor)
        self.input_edit.ensureCursorVisible()

    def _cursor_for_error(self) -> QTextCursor | None:
        document = self.input_edit.document()
        cursor = self.input_edit.textCursor()
        text = self.get_text()

        if self._error_index is not None:
            cursor.setPosition(max(0, min(self._error_index, len(text))))
            return cursor

        if self._error_line is not None:
            block = document.findBlockByLineNumber(max(0, self._error_line - 1))
            if block.isValid():
                cursor.setPosition(block.position() + max(0, (self._error_column or 1) - 1))
                return cursor
        return None

    def _refresh_highlights(self) -> None:
        selections: list[QTextEdit.ExtraSelection] = []
        selections.extend(self._build_diff_selections())
        selections.extend(self._build_search_selections())
        error_selection = self._build_error_selection()
        if error_selection is not None:
            selections.append(error_selection)
        self.input_edit.setExtraSelections(selections)

    def _build_diff_selections(self) -> list[QTextEdit.ExtraSelection]:
        if not self._diff_highlight_enabled:
            return []
        return [
            _make_span_selection(
                self.input_edit,
                start,
                end,
                background=self._theme.diff_background,
                foreground=self._theme.diff_foreground,
            )
            for start, end in self._diff_spans
            if end > start
        ]

    def _build_search_selections(self) -> list[QTextEdit.ExtraSelection]:
        selections: list[QTextEdit.ExtraSelection] = []
        for index, (start, end) in enumerate(self._search_matches):
            is_active = index == self._active_search_index
            selections.append(
                _make_span_selection(
                    self.input_edit,
                    start,
                    end,
                    background=self._theme.search_active_background if is_active else self._theme.search_background,
                    foreground=self._theme.search_active_foreground if is_active else self._theme.search_foreground,
                )
            )
        return selections

    def _build_error_selection(self) -> QTextEdit.ExtraSelection | None:
        cursor = self._cursor_for_error()
        if cursor is None:
            return None
        selection = QTextEdit.ExtraSelection()
        selection.cursor = QTextCursor(cursor)
        selection.cursor.clearSelection()
        selection.cursor.select(QTextCursor.LineUnderCursor)
        selection.format.setBackground(qcolor(self._theme.parse_error_background))
        selection.format.setForeground(qcolor(self._theme.parse_error_foreground))
        selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        return selection

    def _render_summary(self) -> None:
        summary_text = "\n".join(f"- {render_ui_message(self._language, item)}" for item in self._summary_messages)
        warning_text = "\n".join(f"- {render_ui_warning(self._language, item)}" for item in self._warning_messages)
        self.summary_edit.setPlainText(summary_text)
        self.warning_edit.setPlainText(warning_text)
        self.summary_label.setVisible(bool(self._summary_messages))
        self.summary_edit.setVisible(bool(self._summary_messages))
        self.warning_label.setVisible(bool(self._warning_messages))
        self.warning_edit.setVisible(bool(self._warning_messages))
        self._set_risk_badge(self._risk_level)

    def _reset_summary_widgets(self) -> None:
        self.summary_edit.clear()
        self.warning_edit.clear()
        self.summary_label.setVisible(False)
        self.summary_edit.setVisible(False)
        self.warning_label.setVisible(False)
        self.warning_edit.setVisible(False)
        self._set_risk_badge(None)

    def _set_risk_badge(self, risk_level: str | None) -> None:
        if not risk_level:
            self.risk_badge.clear()
            self.risk_badge.setVisible(False)
            self.risk_badge.setStyleSheet("")
            return

        palette = {
            "low": "#2e7d32",
            "medium": "#ef6c00",
            "high": "#c62828",
        }
        color = palette.get(risk_level, self._theme.accent)
        self.risk_badge.setText(translate(self._language, "label.risk", level=risk_level.capitalize()))
        self.risk_badge.setStyleSheet(
            f"QLabel {{ background: {color}; color: white; padding: 4px 8px; border-radius: 4px; }}"
        )
        self.risk_badge.setVisible(True)


def _find_text_matches(text: str, term: str) -> list[tuple[int, int]]:
    normalized = term.strip().lower()
    if not normalized:
        return []

    haystack = text.lower()
    matches: list[tuple[int, int]] = []
    start = 0
    while True:
        index = haystack.find(normalized, start)
        if index < 0:
            break
        matches.append((index, index + len(normalized)))
        start = index + len(normalized)
    return matches


def _make_span_selection(
    editor: QTextEdit,
    start: int,
    end: int,
    *,
    background: str,
    foreground: str,
) -> QTextEdit.ExtraSelection:
    selection = QTextEdit.ExtraSelection()
    cursor = editor.textCursor()
    cursor.setPosition(start)
    cursor.setPosition(end, QTextCursor.KeepAnchor)
    selection.cursor = cursor
    selection.format.setBackground(QColor(background))
    selection.format.setForeground(QColor(foreground))
    return selection
