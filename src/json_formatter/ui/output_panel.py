from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QFont, QTextCursor
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from .highlighter import JsonSyntaxHighlighter
from .input_panel import ZoomableTextEdit


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.title_label = QLabel("Formatted / Repaired Output", self)
        self.output_edit = ZoomableTextEdit(self)
        self.output_edit.setAcceptRichText(False)
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Formatted JSON will appear here")
        self.output_edit.setStyleSheet("QTextEdit { background: #fbfcfe; }")
        self.output_highlighter = JsonSyntaxHighlighter(self.output_edit.document())

        layout.addWidget(self.title_label)
        layout.addWidget(self.output_edit, 1)

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
    ) -> None:
        self._state = OutputState(
            text=text,
            status_text=status_text,
            has_success=success,
            default_filename=default_filename,
        )
        self.output_edit.setPlainText(text)
        self.output_edit.moveCursor(QTextCursor.Start)

    def clear_output(self) -> None:
        self._state = OutputState()
        self.output_edit.clear()

    def set_error_state(self, *, status_text: str) -> None:
        self._state = OutputState(
            text=self._state.text,
            status_text=status_text,
            has_success=False,
            default_filename=self._state.default_filename,
        )

    # Extension points for later phases.
    def set_summary(self, *_args: object, **_kwargs: object) -> None:
        return None

    def set_tree_value(self, *_args: object, **_kwargs: object) -> None:
        return None
