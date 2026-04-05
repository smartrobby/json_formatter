from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
)

from .highlighter import JsonSyntaxHighlighter
from .input_panel import ZoomableTextEdit
from .json_tree_view import JsonTreeView


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.title_label = QLabel("Formatted / Repaired Output", self)
        self.risk_badge = QLabel("", self)
        self.risk_badge.setVisible(False)

        self.summary_label = QLabel("Change Summary", self)
        self.summary_edit = QTextEdit(self)
        self.summary_edit.setReadOnly(True)
        self.summary_edit.setPlaceholderText("Repair changes will appear here")
        self.summary_edit.setMaximumHeight(90)

        self.warning_label = QLabel("Warnings", self)
        self.warning_edit = QTextEdit(self)
        self.warning_edit.setReadOnly(True)
        self.warning_edit.setPlaceholderText("Repair warnings will appear here")
        self.warning_edit.setMaximumHeight(90)

        self.tab_widget = QTabWidget(self)

        text_tab = QWidget(self.tab_widget)
        text_tab_layout = QVBoxLayout(text_tab)
        text_tab_layout.setContentsMargins(0, 0, 0, 0)
        self.output_edit = ZoomableTextEdit(text_tab)
        self.output_edit.setAcceptRichText(False)
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Formatted JSON will appear here")
        self.output_edit.setStyleSheet("QTextEdit { background: #fbfcfe; }")
        self.output_highlighter = JsonSyntaxHighlighter(self.output_edit.document())
        text_tab_layout.addWidget(self.output_edit, 1)

        tree_tab = QWidget(self.tab_widget)
        tree_tab_layout = QVBoxLayout(tree_tab)
        tree_tab_layout.setContentsMargins(0, 0, 0, 0)
        tree_tab_layout.setSpacing(6)

        search_row = QHBoxLayout()
        search_row.setContentsMargins(0, 0, 0, 0)
        search_row.setSpacing(6)
        self.search_input = QLineEdit(tree_tab)
        self.search_input.setPlaceholderText("Search key, value, or path")
        self.search_result_label = QLabel("0 matches", tree_tab)
        self.copy_path_button = QPushButton("Copy Path", tree_tab)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_result_label)
        search_row.addWidget(self.copy_path_button)

        self.tree_view = JsonTreeView(tree_tab)
        self.selected_path_label = QLabel("Selected path: ", tree_tab)

        tree_tab_layout.addLayout(search_row)
        tree_tab_layout.addWidget(self.tree_view, 1)
        tree_tab_layout.addWidget(self.selected_path_label)

        self.tab_widget.addTab(text_tab, "Text View")
        self.tab_widget.addTab(tree_tab, "Tree View")

        layout.addWidget(self.title_label)
        layout.addWidget(self.risk_badge)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.summary_edit)
        layout.addWidget(self.warning_label)
        layout.addWidget(self.warning_edit)
        layout.addWidget(self.tab_widget, 1)

        self.search_input.textChanged.connect(self._apply_search)
        self.tree_view.currentItemChanged.connect(lambda *_args: self._update_selected_path())
        self.copy_path_button.clicked.connect(self.copy_selected_path)
        self._reset_summary_widgets()

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

    def clear_output(self) -> None:
        self._state = OutputState()
        self._parsed_value = None
        self.output_edit.clear()
        self.tree_view.clear()
        self.search_input.clear()
        self._update_selected_path()
        self._reset_summary_widgets()

    def set_error_state(self, *, status_text: str) -> None:
        self._state = OutputState(
            text=self._state.text,
            status_text=status_text,
            has_success=False,
            default_filename=self._state.default_filename,
        )

    def set_summary(
        self,
        change_summary: list[str],
        repair_warnings: list[str],
        risk_level: str | None,
    ) -> None:
        summary_text = "\n".join(f"- {item}" for item in change_summary)
        warning_text = "\n".join(f"- {item}" for item in repair_warnings)
        self.summary_edit.setPlainText(summary_text)
        self.warning_edit.setPlainText(warning_text)
        self.summary_edit.setVisible(bool(change_summary))
        self.summary_label.setVisible(bool(change_summary))
        self.warning_edit.setVisible(bool(repair_warnings))
        self.warning_label.setVisible(bool(repair_warnings))
        self._set_risk_badge(risk_level)

    def set_tree_value(self, value: object | None) -> None:
        self._parsed_value = value
        self.tree_view.set_json_value(value)
        self._apply_search(self.search_input.text())
        self._update_selected_path()

    def copy_selected_path(self) -> None:
        path = self.tree_view.selected_json_path()
        if not path:
            return
        QApplication.clipboard().setText(path)

    def _apply_search(self, term: str) -> None:
        matches = self.tree_view.apply_search(term)
        self.search_result_label.setText(f"{matches} matches")
        self._update_selected_path()

    def _update_selected_path(self) -> None:
        path = self.tree_view.selected_json_path()
        self.selected_path_label.setText(f"Selected path: {path}")

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
        color = palette.get(risk_level, "#455a64")
        self.risk_badge.setText(f"Risk: {risk_level.capitalize()}")
        self.risk_badge.setStyleSheet(
            f"QLabel {{ background: {color}; color: white; padding: 4px 8px; border-radius: 4px; }}"
        )
        self.risk_badge.setVisible(True)
