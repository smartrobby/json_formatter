from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


@dataclass(slots=True)
class OutputState:
    text: str = ""
    status_text: str = "Ready"
    has_success: bool = False
    default_filename: str = "formatted.json"


class MainWindow(QMainWindow):
    formatRequested = Signal(str)
    repairRequested = Signal(str)
    copyRequested = Signal(str)
    saveRequested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("JSON Viewer & Formatter")
        self.resize(1280, 800)

        self._output_state = OutputState()
        self.controller = None

        self._build_ui()
        self._wire_actions()
        self._apply_default_state()

    def _build_ui(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(12, 12, 12, 12)
        root_layout.setSpacing(10)

        toolbar = QFrame(central)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        toolbar_layout.setSpacing(8)

        self.format_button = QPushButton("Format", toolbar)
        self.repair_button = QPushButton("Repair", toolbar)
        self.copy_button = QPushButton("Copy Output", toolbar)
        self.save_button = QPushButton("Save Output", toolbar)

        toolbar_layout.addWidget(self.format_button)
        toolbar_layout.addWidget(self.repair_button)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.copy_button)
        toolbar_layout.addWidget(self.save_button)

        self.splitter = QSplitter(Qt.Horizontal, central)
        self.splitter.setChildrenCollapsible(False)

        left_panel = QWidget(self.splitter)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)
        left_layout.addWidget(QLabel("Raw JSON Input", left_panel))

        self.input_edit = QTextEdit(left_panel)
        self.input_edit.setAcceptRichText(False)
        self.input_edit.setPlaceholderText("Paste or type JSON here")
        left_layout.addWidget(self.input_edit, 1)

        right_panel = QWidget(self.splitter)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)
        right_layout.addWidget(QLabel("Formatted / Repaired Output", right_panel))

        self.output_edit = QTextEdit(right_panel)
        self.output_edit.setAcceptRichText(False)
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("Formatted JSON will appear here")
        right_layout.addWidget(self.output_edit, 1)

        root_layout.addWidget(toolbar)
        root_layout.addWidget(self.splitter, 1)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready", self.status_bar)
        self.status_bar.addPermanentWidget(self.status_label)

        self.error_label = QLabel("", self.status_bar)
        self.error_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_bar.addWidget(self.error_label, 1)

        self._apply_monospace_font()
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([1, 1])

    def _apply_monospace_font(self) -> None:
        font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Courier New")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(10)
        self.input_edit.setFont(font)
        self.output_edit.setFont(font)

    def _wire_actions(self) -> None:
        self.format_button.clicked.connect(self._emit_format_requested)
        self.repair_button.clicked.connect(self._emit_repair_requested)
        self.copy_button.clicked.connect(self.copy_output_to_clipboard)
        self.save_button.clicked.connect(self.save_output_to_file)

        self.input_edit.textChanged.connect(self._sync_output_buttons_state)

        self.format_shortcut = QShortcut(QKeySequence("Ctrl+Return"), self)
        self.format_shortcut.activated.connect(self._emit_format_requested)

        self.repair_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Return"), self)
        self.repair_shortcut.activated.connect(self._emit_repair_requested)

        self.save_shortcut = QShortcut(QKeySequence.Save, self)
        self.save_shortcut.activated.connect(self.save_output_to_file)

    def _apply_default_state(self) -> None:
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.set_status("Ready")
        self.set_error("")

    def _emit_format_requested(self) -> None:
        self.formatRequested.emit(self.input_edit.toPlainText())

    def _emit_repair_requested(self) -> None:
        self.repairRequested.emit(self.input_edit.toPlainText())

    def _sync_output_buttons_state(self) -> None:
        self.copy_button.setEnabled(self._output_state.has_success and bool(self._output_state.text))
        self.save_button.setEnabled(self._output_state.has_success and bool(self._output_state.text))

    def set_input_text(self, text: str) -> None:
        self.input_edit.setPlainText(text)

    def get_input_text(self) -> str:
        return self.input_edit.toPlainText()

    def get_output_text(self) -> str:
        return self.output_edit.toPlainText()

    def set_output_text(
        self,
        text: str,
        *,
        status_text: str = "Ready",
        success: bool = True,
        default_filename: str = "formatted.json",
    ) -> None:
        self._output_state = OutputState(
            text=text,
            status_text=status_text,
            has_success=success,
            default_filename=default_filename,
        )
        self.output_edit.setPlainText(text)
        self.output_edit.moveCursor(QTextCursor.Start)
        self.set_status(status_text)
        self.set_error("")
        self._sync_output_buttons_state()

    def clear_output(self, *, status_text: str = "Ready", error_text: str = "") -> None:
        self._output_state = OutputState()
        self.output_edit.clear()
        self.set_status(status_text)
        self.set_error(error_text)
        self._sync_output_buttons_state()

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_error(self, text: str) -> None:
        self.error_label.setText(text)
        self.status_bar.setStyleSheet("QStatusBar { color: #b00020; }" if text else "")

    def set_processing(self, processing: bool) -> None:
        self.format_button.setEnabled(not processing)
        self.repair_button.setEnabled(not processing)
        self.input_edit.setReadOnly(processing)
        if processing:
            self.set_status("Processing...")
        elif self._output_state.has_success:
            self.set_status(self._output_state.status_text)
        else:
            self.set_status("Ready")

    def set_success_state(
        self,
        output_text: str,
        status_text: str = "Success",
        default_filename: str = "formatted.json",
    ) -> None:
        self.set_output_text(
            output_text,
            status_text=status_text,
            success=True,
            default_filename=default_filename,
        )

    def set_error_state(self, error_text: str, status_text: str = "Error") -> None:
        self._output_state = OutputState(text=self._output_state.text, status_text=status_text, has_success=False)
        self.set_status(status_text)
        self.set_error(error_text)
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def copy_output_to_clipboard(self) -> None:
        text = self.get_output_text()
        if not text:
            self._show_warning("No output available to copy.")
            return
        QApplication.clipboard().setText(text)
        self.copyRequested.emit(text)
        self.set_status("Copied output to clipboard")

    def save_output_to_file(self) -> None:
        text = self.get_output_text()
        if not text:
            self._show_warning("No output available to save.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON Output",
            self._output_state.default_filename,
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        except OSError as exc:
            self._show_warning(f"Failed to save file: {exc}")
            return

        self.saveRequested.emit(path)
        self.set_status(f"Saved to {path}")

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, "JSON Viewer & Formatter", message)
