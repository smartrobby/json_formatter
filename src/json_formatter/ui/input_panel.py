from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QFont, QKeySequence, QShortcut, QTextCharFormat, QTextCursor, QWheelEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..models import RepairMode

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QWidget(self)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(8)

        self.title_label = QLabel("Raw JSON Input", header)
        self.open_button = QPushButton("Open File", header)
        self.mode_label = QLabel("Repair Mode", header)
        self.mode_combo = QComboBox(header)
        self.mode_combo.addItem("Strict", "strict")
        self.mode_combo.addItem("Safe", "safe")
        self.mode_combo.addItem("Aggressive", "aggressive")

        header_layout.addWidget(self.title_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self.open_button)
        header_layout.addWidget(self.mode_label)
        header_layout.addWidget(self.mode_combo)

        self.input_edit = ZoomableTextEdit(self)
        self.input_edit.setAcceptRichText(False)
        self.input_edit.setPlaceholderText("Paste or type JSON here")
        self.open_shortcut = QShortcut(QKeySequence.Open, self)

        layout.addWidget(header)
        layout.addWidget(self.input_edit, 1)
        self._restore_repair_mode()
        self._wire_actions()
        self.clear_error_highlight()

    def _create_settings(self) -> QSettings:
        return QSettings()

    def _wire_actions(self) -> None:
        self.open_button.clicked.connect(self._emit_open_file_requested)
        self.open_shortcut.activated.connect(self._emit_open_file_requested)
        self.mode_combo.currentIndexChanged.connect(self._handle_mode_changed)

    def _load_last_open_path(self) -> str:
        raw_value = self._settings.value(LAST_OPEN_PATH_KEY, "")
        if isinstance(raw_value, str):
            return raw_value
        return ""

    def _restore_repair_mode(self) -> None:
        stored_mode = str(self._settings.value(REPAIR_MODE_KEY, "safe"))
        index = self.mode_combo.findData(stored_mode)
        if index < 0:
            index = self.mode_combo.findData("safe")
        self.mode_combo.setCurrentIndex(index)

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

    def clear_error_highlight(self) -> None:
        self.input_edit.setExtraSelections([])

    def highlight_error(
        self,
        *,
        line: int | None = None,
        column: int | None = None,
        index: int | None = None,
    ) -> None:
        document = self.input_edit.document()
        cursor = self.input_edit.textCursor()

        if index is not None:
            cursor.setPosition(max(0, min(index, len(self.get_text()))))
        elif line is not None:
            block = document.findBlockByLineNumber(max(0, line - 1))
            if block.isValid():
                block_position = block.position()
                column_offset = max(0, (column or 1) - 1)
                cursor.setPosition(block_position + column_offset)
            else:
                cursor.movePosition(QTextCursor.Start)
        else:
            cursor.movePosition(QTextCursor.Start)

        self.input_edit.setTextCursor(cursor)
        self.input_edit.ensureCursorVisible()

        selection = QTextEdit.ExtraSelection()
        selection.cursor = QTextCursor(cursor)
        selection.cursor.clearSelection()
        selection.cursor.select(QTextCursor.LineUnderCursor)
        selection.format.setBackground(QColor("#ffe7e8"))
        selection.format.setProperty(QTextCharFormat.FullWidthSelection, True)
        self.input_edit.setExtraSelections([selection])

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
