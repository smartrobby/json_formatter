from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import ThemeMode, UiLanguage, UiMessage
from .highlighter import JsonSyntaxHighlighter
from .input_panel import ZoomableTextEdit, _find_text_matches, _make_span_selection
from .json_tree_view import JsonTreeView
from .localization import render_ui_message, render_ui_warning, translate
from .search_bar import InlineSearchBar
from .theme import ThemeSpec, get_theme, qcolor


@dataclass(slots=True)
class OutputState:
    text: str = ""
    status_text: str = "Ready"
    has_success: bool = False
    default_filename: str = "formatted.json"


class OutputPanel(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._state = OutputState()
        self._parsed_value: object | None = None
        self._language: UiLanguage = "ko"
        self._theme_mode: ThemeMode = "system"
        self._theme: ThemeSpec = get_theme("system")
        self._summary_messages: list[UiMessage] = []
        self._warning_messages: list[UiMessage] = []
        self._risk_level: str | None = None
        self._text_diff_spans: list[tuple[int, int]] = []
        self._diff_highlight_enabled = True
        self._text_search_matches: list[tuple[int, int]] = []
        self._active_text_search_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)
        self.title_label = QLabel(self)
        self.risk_badge = QLabel("", self)
        self.risk_badge.setVisible(False)
        header_row.addWidget(self.title_label)
        header_row.addStretch(1)
        header_row.addWidget(self.risk_badge)

        self.summary_label = QLabel(self)
        self.summary_edit = QTextEdit(self)
        self.summary_edit.setReadOnly(True)
        self.summary_edit.setMaximumHeight(90)

        self.warning_label = QLabel(self)
        self.warning_edit = QTextEdit(self)
        self.warning_edit.setReadOnly(True)
        self.warning_edit.setMaximumHeight(90)

        self.tab_widget = QTabWidget(self)

        text_tab = QWidget(self.tab_widget)
        text_tab_layout = QVBoxLayout(text_tab)
        text_tab_layout.setContentsMargins(0, 0, 0, 0)
        text_tab_layout.setSpacing(6)

        text_header = QHBoxLayout()
        text_header.setContentsMargins(0, 0, 0, 0)
        text_header.setSpacing(8)
        self.text_search_button = QPushButton(text_tab)
        text_header.addStretch(1)
        text_header.addWidget(self.text_search_button)

        self.text_search_bar = InlineSearchBar(text_tab)
        self.output_edit = ZoomableTextEdit(text_tab)
        self.output_edit.setAcceptRichText(False)
        self.output_edit.setReadOnly(True)
        self.output_highlighter = JsonSyntaxHighlighter(self.output_edit.document())

        text_tab_layout.addLayout(text_header)
        text_tab_layout.addWidget(self.text_search_bar)
        text_tab_layout.addWidget(self.output_edit, 1)

        tree_tab = QWidget(self.tab_widget)
        tree_tab_layout = QVBoxLayout(tree_tab)
        tree_tab_layout.setContentsMargins(0, 0, 0, 0)
        tree_tab_layout.setSpacing(6)

        tree_header = QHBoxLayout()
        tree_header.setContentsMargins(0, 0, 0, 0)
        tree_header.setSpacing(8)
        self.tree_search_button = QPushButton(tree_tab)
        self.expand_all_button = QPushButton(tree_tab)
        self.collapse_all_button = QPushButton(tree_tab)
        self.copy_path_button = QPushButton(tree_tab)
        tree_header.addStretch(1)
        tree_header.addWidget(self.tree_search_button)
        tree_header.addWidget(self.expand_all_button)
        tree_header.addWidget(self.collapse_all_button)
        tree_header.addWidget(self.copy_path_button)

        self.tree_search_bar = InlineSearchBar(tree_tab)
        self.tree_view = JsonTreeView(tree_tab)
        self.selected_path_label = QLabel(tree_tab)

        tree_tab_layout.addLayout(tree_header)
        tree_tab_layout.addWidget(self.tree_search_bar)
        tree_tab_layout.addWidget(self.tree_view, 1)
        tree_tab_layout.addWidget(self.selected_path_label)

        self.tab_widget.addTab(text_tab, "")
        self.tab_widget.addTab(tree_tab, "")

        layout.addLayout(header_row)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.summary_edit)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.warning_edit)
        layout.addWidget(self.tab_widget, 1)

        self.text_search_button.clicked.connect(self.show_text_search)
        self.tree_search_button.clicked.connect(self.show_tree_search)
        self.expand_all_button.clicked.connect(self.tree_view.expandAll)
        self.collapse_all_button.clicked.connect(self.tree_view.collapseAll)
        self.copy_path_button.clicked.connect(self.copy_selected_path)
        self.text_search_bar.query_edit.textChanged.connect(self._handle_text_search_changed)
        self.text_search_bar.nextRequested.connect(lambda: self._move_text_search(1))
        self.text_search_bar.previousRequested.connect(lambda: self._move_text_search(-1))
        self.text_search_bar.closed.connect(self._handle_text_search_closed)
        self.tree_search_bar.query_edit.textChanged.connect(self._handle_tree_search_changed)
        self.tree_search_bar.nextRequested.connect(self._handle_tree_next)
        self.tree_search_bar.previousRequested.connect(self._handle_tree_previous)
        self.tree_search_bar.closed.connect(self._handle_tree_search_closed)
        self.tree_view.currentItemChanged.connect(lambda *_args: self._update_selected_path())

        self.apply_language("ko")
        self.apply_theme(self._theme)
        self._reset_summary_widgets()

    def apply_language(self, language: UiLanguage) -> None:
        self._language = language
        self.title_label.setText(translate(language, "label.output_title"))
        self.summary_label.setText(translate(language, "label.summary"))
        self.warning_label.setText(translate(language, "label.warnings"))
        self.summary_edit.setPlaceholderText(translate(language, "placeholder.summary"))
        self.warning_edit.setPlaceholderText(translate(language, "placeholder.warnings"))
        self.text_search_button.setText(translate(language, "button.search"))
        self.tree_search_button.setText(translate(language, "button.search"))
        self.expand_all_button.setText(translate(language, "button.expand_all"))
        self.collapse_all_button.setText(translate(language, "button.collapse_all"))
        self.copy_path_button.setText(translate(language, "button.copy_path"))
        self.text_search_bar.apply_language(language)
        self.tree_search_bar.apply_language(language)
        self.tree_view.apply_language(language)
        self.tab_widget.setTabText(0, translate(language, "label.text_view"))
        self.tab_widget.setTabText(1, translate(language, "label.tree_view"))
        self._render_summary()
        self._update_selected_path()

    def apply_theme(self, theme: ThemeSpec) -> None:
        self._theme = theme
        self.setStyleSheet(
            (
                "QWidget {"
                f" color: {theme.foreground};"
                " }"
                "QPushButton {"
                f" background: {theme.surface_background};"
                f" color: {theme.foreground};"
                f" border: 1px solid {theme.border};"
                " padding: 4px 8px; }"
                "QTabWidget::pane {"
                f" border: 1px solid {theme.border};"
                f" background: {theme.surface_background};"
                " }"
                "QTabBar::tab {"
                f" background: {theme.surface_alt_background};"
                f" color: {theme.foreground};"
                f" border: 1px solid {theme.border};"
                " padding: 6px 10px; }"
                "QTabBar::tab:selected {"
                f" background: {theme.surface_background};"
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
        self.output_edit.setStyleSheet(
            (
                "QTextEdit {"
                f" background: {theme.output_background};"
                f" color: {theme.foreground};"
                f" border: 1px solid {theme.border};"
                f" selection-background-color: {theme.selection_background};"
                f" selection-color: {theme.selection_foreground};"
                " }"
            )
        )
        self.output_highlighter.apply_theme(theme)
        self.text_search_bar.apply_theme(theme)
        self.tree_search_bar.apply_theme(theme)
        self.tree_view.apply_theme(theme)
        self._refresh_text_highlights()
        self._set_risk_badge(self._risk_level)

    def apply_editor_font(self, font: QFont) -> None:
        self.output_edit.setFont(font)

    def get_text(self) -> str:
        return self.output_edit.toPlainText()

    @property
    def text(self) -> str:
        return self._state.text

    @property
    def status_text(self) -> str:
        return self._state.status_text

    @property
    def has_success(self) -> bool:
        return self._state.has_success

    @property
    def default_filename(self) -> str:
        return self._state.default_filename

    def mark_stale(self) -> None:
        self._state = OutputState(
            text=self._state.text,
            status_text="Updating...",
            has_success=False,
            default_filename=self._state.default_filename,
        )

    def set_output_text(
        self,
        text: str,
        *,
        status_text: str = "Ready",
        success: bool = True,
        default_filename: str = "formatted.json",
        parsed_value: object | None = None,
    ) -> None:
        self._state = OutputState(
            text=text,
            status_text=status_text,
            has_success=success,
            default_filename=default_filename,
        )
        self.output_edit.setPlainText(text)
        self.output_edit.moveCursor(QTextCursor.Start)
        if parsed_value is not None:
            self.set_tree_value(parsed_value)
        if self.text_search_bar.query_edit.text():
            self._handle_text_search_changed(self.text_search_bar.query_edit.text())
        self._refresh_text_highlights()

    def clear_output(self) -> None:
        self._state = OutputState()
        self._parsed_value = None
        self._summary_messages = []
        self._warning_messages = []
        self._risk_level = None
        self._text_diff_spans = []
        self._text_search_matches = []
        self._active_text_search_index = -1
        self.output_edit.clear()
        self.tree_view.clear()
        self.text_search_bar.hide()
        self.tree_search_bar.hide()
        self.text_search_bar.query_edit.clear()
        self.tree_search_bar.query_edit.clear()
        self._update_selected_path()
        self._reset_summary_widgets()
        self._refresh_text_highlights()

    def set_error_state(self, *, status_text: str) -> None:
        self._state = OutputState(
            text=self._state.text,
            status_text=status_text,
            has_success=False,
            default_filename=self._state.default_filename,
        )
        self.clear_text_diff()

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

    def set_tree_value(self, value: object | None) -> None:
        self._parsed_value = value
        self.tree_view.set_json_value(value)
        self._handle_tree_search_changed(self.tree_search_bar.query_edit.text())
        self._update_selected_path()

    def set_text_diff(self, spans: list[tuple[int, int]]) -> None:
        self._text_diff_spans = spans
        self._refresh_text_highlights()

    def clear_text_diff(self) -> None:
        self._text_diff_spans = []
        self._refresh_text_highlights()

    def set_diff_highlight_enabled(self, enabled: bool) -> None:
        self._diff_highlight_enabled = enabled
        self._refresh_text_highlights()

    def show_text_search(self) -> None:
        self.tab_widget.setCurrentIndex(0)
        self.text_search_bar.open_bar()

    def show_tree_search(self) -> None:
        self.tab_widget.setCurrentIndex(1)
        self.tree_search_bar.open_bar()

    def copy_selected_path(self) -> None:
        path = self.tree_view.selected_json_path()
        if not path:
            return
        QApplication.clipboard().setText(path)

    def _handle_text_search_changed(self, term: str) -> None:
        self._text_search_matches = _find_text_matches(self.get_text(), term)
        self._active_text_search_index = 0 if self._text_search_matches else -1
        self.text_search_bar.set_result_state(
            len(self._text_search_matches),
            self._active_text_search_index + 1 if self._text_search_matches else 0,
        )
        self._focus_text_search()
        self._refresh_text_highlights()

    def _handle_text_search_closed(self) -> None:
        self.text_search_bar.query_edit.blockSignals(True)
        self.text_search_bar.query_edit.clear()
        self.text_search_bar.query_edit.blockSignals(False)
        self._text_search_matches = []
        self._active_text_search_index = -1
        self._refresh_text_highlights()

    def _move_text_search(self, direction: int) -> None:
        if not self._text_search_matches:
            return
        self._active_text_search_index = (self._active_text_search_index + direction) % len(self._text_search_matches)
        self.text_search_bar.set_result_state(len(self._text_search_matches), self._active_text_search_index + 1)
        self._focus_text_search()
        self._refresh_text_highlights()

    def _focus_text_search(self) -> None:
        if self._active_text_search_index < 0 or not self._text_search_matches:
            return
        start, end = self._text_search_matches[self._active_text_search_index]
        cursor = self.output_edit.textCursor()
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.KeepAnchor)
        self.output_edit.setTextCursor(cursor)
        self.output_edit.ensureCursorVisible()

    def _handle_tree_search_changed(self, term: str) -> None:
        total, current = self.tree_view.set_search_term(term)
        self.tree_search_bar.set_result_state(total, current)
        self._update_selected_path()

    def _handle_tree_next(self) -> None:
        total, current = self.tree_view.select_next_match()
        self.tree_search_bar.set_result_state(total, current)
        self._update_selected_path()

    def _handle_tree_previous(self) -> None:
        total, current = self.tree_view.select_previous_match()
        self.tree_search_bar.set_result_state(total, current)
        self._update_selected_path()

    def _handle_tree_search_closed(self) -> None:
        self.tree_search_bar.query_edit.blockSignals(True)
        self.tree_search_bar.query_edit.clear()
        self.tree_search_bar.query_edit.blockSignals(False)
        self.tree_view.set_search_term("")
        self.tree_search_bar.set_result_state(0, 0)
        self._update_selected_path()

    def _refresh_text_highlights(self) -> None:
        selections = []
        if self._diff_highlight_enabled:
            selections.extend(
                [
                    _make_span_selection(
                        self.output_edit,
                        start,
                        end,
                        background=self._theme.diff_background,
                        foreground=self._theme.diff_foreground,
                    )
                    for start, end in self._text_diff_spans
                    if end > start
                ]
            )
        for index, (start, end) in enumerate(self._text_search_matches):
            selections.append(
                _make_span_selection(
                    self.output_edit,
                    start,
                    end,
                    background=self._theme.search_active_background if index == self._active_text_search_index else self._theme.search_background,
                    foreground=self._theme.search_active_foreground if index == self._active_text_search_index else self._theme.search_foreground,
                )
            )
        self.output_edit.setExtraSelections(selections)

    def _update_selected_path(self) -> None:
        path = self.tree_view.selected_json_path()
        self.selected_path_label.setText(translate(self._language, "label.selected_path", path=path))

    def _render_summary(self) -> None:
        summary_text = "\n".join(f"- {render_ui_message(self._language, item)}" for item in self._summary_messages)
        warning_text = "\n".join(f"- {render_ui_warning(self._language, item)}" for item in self._warning_messages)
        self.summary_edit.setPlainText(summary_text)
        self.warning_edit.setPlainText(warning_text)
        self.summary_edit.setVisible(bool(self._summary_messages))
        self.summary_label.setVisible(bool(self._summary_messages))
        self.warning_edit.setVisible(bool(self._warning_messages))
        self.warning_label.setVisible(bool(self._warning_messages))
        self._set_risk_badge(self._risk_level)

    def _reset_summary_widgets(self) -> None:
        self.summary_edit.clear()
        self.warning_edit.clear()
        self.summary_edit.setVisible(False)
        self.warning_edit.setVisible(False)
        self.summary_label.setVisible(False)
        self.warning_label.setVisible(False)
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
