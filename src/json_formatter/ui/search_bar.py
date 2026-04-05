from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from ..models import UiLanguage
from .localization import translate
from .theme import ThemeSpec


class SearchLineEdit(QLineEdit):
    previousRequested = Signal()
    nextRequested = Signal()
    closeRequested = Signal()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ShiftModifier:
                self.previousRequested.emit()
            else:
                self.nextRequested.emit()
            event.accept()
            return

        if event.key() == Qt.Key_Escape:
            self.closeRequested.emit()
            event.accept()
            return

        super().keyPressEvent(event)


class InlineSearchBar(QWidget):
    previousRequested = Signal()
    nextRequested = Signal()
    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._language: UiLanguage = "ko"
        self._theme: ThemeSpec | None = None
        self._result_total = 0
        self._result_index = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.query_edit = SearchLineEdit(self)
        self.previous_button = QPushButton(self)
        self.next_button = QPushButton(self)
        self.result_label = QLabel(self)
        self.close_button = QPushButton(self)

        layout.addWidget(self.query_edit, 1)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.close_button)

        self.query_edit.textChanged.connect(self._refresh_result_label)
        self.query_edit.previousRequested.connect(self.previousRequested.emit)
        self.query_edit.nextRequested.connect(self.nextRequested.emit)
        self.query_edit.closeRequested.connect(self.close_bar)
        self.previous_button.clicked.connect(self.previousRequested.emit)
        self.next_button.clicked.connect(self.nextRequested.emit)
        self.close_button.clicked.connect(self.close_bar)
        self.hide()
        self.apply_language("ko")

    def apply_language(self, language: UiLanguage) -> None:
        self._language = language
        self.query_edit.setPlaceholderText(translate(language, "label.search_placeholder"))
        self.previous_button.setText(translate(language, "button.prev"))
        self.next_button.setText(translate(language, "button.next"))
        self.close_button.setText(translate(language, "button.close"))
        self._refresh_result_label()

    def apply_theme(self, theme: ThemeSpec) -> None:
        self._theme = theme
        self.setStyleSheet(
            "\n".join(
                [
                    f"QWidget {{ background: {theme.surface_background}; color: {theme.foreground}; }}",
                    (
                        "QLineEdit, QPushButton {"
                        f" background: {theme.surface_alt_background};"
                        f" color: {theme.foreground};"
                        f" border: 1px solid {theme.border};"
                        " padding: 4px 6px; }"
                    ),
                    f"QLabel {{ color: {theme.muted_foreground}; }}",
                ]
            )
        )

    def open_bar(self) -> None:
        self.show()
        self.query_edit.setFocus()
        self.query_edit.selectAll()

    def close_bar(self) -> None:
        self.hide()
        self.closed.emit()

    def set_result_state(self, total: int, current_index: int = 0) -> None:
        self._result_total = total
        self._result_index = current_index
        self._refresh_result_label()

    def _refresh_result_label(self) -> None:
        if not self.query_edit.text().strip() or self._result_total <= 0:
            self.result_label.setText(translate(self._language, "label.search_none"))
            return

        if self._result_index <= 0:
            self.result_label.setText(translate(self._language, "label.tree_matches", count=self._result_total))
            return

        self.result_label.setText(
            translate(
                self._language,
                "label.search_progress",
                current=self._result_index,
                total=self._result_total,
            )
        )
