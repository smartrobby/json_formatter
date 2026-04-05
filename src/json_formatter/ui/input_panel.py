from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QWheelEvent
from PySide6.QtWidgets import QLabel, QTextEdit, QVBoxLayout, QWidget


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
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.title_label = QLabel("Raw JSON Input", self)
        self.input_edit = ZoomableTextEdit(self)
        self.input_edit.setAcceptRichText(False)
        self.input_edit.setPlaceholderText("Paste or type JSON here")

        layout.addWidget(self.title_label)
        layout.addWidget(self.input_edit, 1)

    def apply_editor_font(self, font: QFont) -> None:
        self.input_edit.setFont(font)

    def set_text(self, text: str) -> None:
        self.input_edit.setPlainText(text)

    def get_text(self) -> str:
        return self.input_edit.toPlainText()

    # Extension points for later phases.
    def clear_error_highlight(self) -> None:
        return None

    def highlight_error(self, *_args: object, **_kwargs: object) -> None:
        return None
