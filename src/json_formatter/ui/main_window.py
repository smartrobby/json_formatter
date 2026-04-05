from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QTimer, Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
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

from .input_panel import InputPanel
from .output_panel import OutputPanel

DEFAULT_EDITOR_FONT_SIZE = 10
MIN_EDITOR_FONT_SIZE = 8
MAX_EDITOR_FONT_SIZE = 28
INPUT_FONT_SIZE_KEY = "ui/font_size/input"
OUTPUT_FONT_SIZE_KEY = "ui/font_size/output"


class MainWindow(QMainWindow):
    autoProcessRequested = Signal(str)
    copyRequested = Signal(str)
    saveRequested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("JSON Viewer & Formatter")
        self.resize(1280, 800)

        self.controller = None
        self._settings = self._create_settings()
        self._input_font_size = self._load_font_size(
            INPUT_FONT_SIZE_KEY,
            DEFAULT_EDITOR_FONT_SIZE,
        )
        self._output_font_size = self._load_font_size(
            OUTPUT_FONT_SIZE_KEY,
            DEFAULT_EDITOR_FONT_SIZE,
        )
        self.auto_process_timer = QTimer(self)
        self.auto_process_timer.setSingleShot(True)
        self.auto_process_timer.setInterval(200)

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

        self.auto_mode_label = QLabel("Auto format/repair on paste or edit", toolbar)
        self.copy_button = QPushButton("Copy Output", toolbar)
        self.save_button = QPushButton("Save Output", toolbar)

        toolbar_layout.addWidget(self.auto_mode_label)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.copy_button)
        toolbar_layout.addWidget(self.save_button)

        self.splitter = QSplitter(Qt.Horizontal, central)
        self.splitter.setChildrenCollapsible(False)

        self.input_panel = InputPanel(self.splitter)
        self.output_panel = OutputPanel(self.splitter)

        # Preserve existing MainWindow attribute surface for current tests and controller code.
        self.input_edit = self.input_panel.input_edit
        self.output_edit = self.output_panel.output_edit
        self.output_highlighter = self.output_panel.output_highlighter

        root_layout.addWidget(toolbar)
        root_layout.addWidget(self.splitter, 1)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel("Ready", self.status_bar)
        self.status_bar.addPermanentWidget(self.status_label)

        self.error_label = QLabel("", self.status_bar)
        self.error_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.status_bar.addWidget(self.error_label, 1)

        self._apply_all_editor_font_sizes()
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([1, 1])

    def _wire_actions(self) -> None:
        self.copy_button.clicked.connect(self.copy_output_to_clipboard)
        self.save_button.clicked.connect(self.save_output_to_file)

        self.input_edit.textChanged.connect(self._schedule_auto_processing)
        self.auto_process_timer.timeout.connect(self._emit_auto_process_requested)
        self.input_edit.fontZoomRequested.connect(self.adjust_input_font_size)
        self.output_edit.fontZoomRequested.connect(self.adjust_output_font_size)
        self.input_panel.openFileRequested.connect(self.open_input_file_dialog)
        self.input_panel.fileDropped.connect(self.load_input_file)
        self.input_panel.repairModeChanged.connect(self._handle_repair_mode_changed)

        self.save_shortcut = QShortcut(QKeySequence.Save, self)
        self.save_shortcut.activated.connect(self.save_output_to_file)

    def _create_settings(self) -> QSettings:
        app = QApplication.instance()
        if app is not None:
            if not app.organizationName():
                app.setOrganizationName("smartrobby")
            if not app.applicationName():
                app.setApplicationName("JSON Viewer & Formatter")
        return QSettings()

    def _load_font_size(self, key: str, default: int) -> int:
        raw_value = self._settings.value(key, default)
        try:
            return self._clamp_font_size(int(raw_value))
        except (TypeError, ValueError):
            return default

    def _build_monospace_font(self, point_size: int) -> QFont:
        font = QFont("Consolas")
        if not font.exactMatch():
            font = QFont("Courier New")
        font.setStyleHint(QFont.Monospace)
        font.setPointSize(point_size)
        return font

    def _apply_editor_font_size(self, editor: QTextEdit, point_size: int) -> None:
        editor.setFont(self._build_monospace_font(point_size))

    def _apply_all_editor_font_sizes(self) -> None:
        self.input_panel.apply_editor_font(self._build_monospace_font(self._input_font_size))
        self.output_panel.apply_editor_font(self._build_monospace_font(self._output_font_size))

    def _clamp_font_size(self, point_size: int) -> int:
        return max(MIN_EDITOR_FONT_SIZE, min(MAX_EDITOR_FONT_SIZE, point_size))

    def _update_editor_font_size(
        self,
        editor: QTextEdit,
        key: str,
        current_size: int,
        delta: int,
        status_prefix: str,
    ) -> int:
        new_size = self._clamp_font_size(current_size + delta)
        if new_size == current_size:
            return current_size

        self._apply_editor_font_size(editor, new_size)
        self._settings.setValue(key, new_size)
        self._settings.sync()
        self.set_status(f"{status_prefix} font size: {new_size}pt")
        return new_size

    def _apply_default_state(self) -> None:
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.set_status("Ready")
        self.set_error("")

    def _schedule_auto_processing(self) -> None:
        current_text = self.get_input_text()
        if not current_text.strip():
            self.auto_process_timer.stop()
            self.clear_output()
            return

        self._mark_output_stale()
        self.auto_process_timer.start()

    def _emit_auto_process_requested(self) -> None:
        self.autoProcessRequested.emit(self.get_input_text())

    def _sync_output_buttons_state(self) -> None:
        self.copy_button.setEnabled(self.output_panel.has_success and bool(self.output_panel.text))
        self.save_button.setEnabled(self.output_panel.has_success and bool(self.output_panel.text))

    def _mark_output_stale(self) -> None:
        self.output_panel.mark_stale()
        self.output_panel.set_summary([], [], None)
        self.output_panel.set_tree_value(None)
        self.set_status("Updating...")
        self.set_error("")
        self._sync_output_buttons_state()

    def set_input_text(self, text: str) -> None:
        self.input_panel.set_text(text)

    def get_input_text(self) -> str:
        return self.input_panel.get_text()

    def get_output_text(self) -> str:
        return self.output_panel.get_text()

    def current_repair_mode(self) -> str:
        return self.input_panel.current_repair_mode()

    def highlight_input_error(
        self,
        *,
        line: int | None = None,
        column: int | None = None,
        index: int | None = None,
    ) -> None:
        self.input_panel.highlight_error(line=line, column=column, index=index)

    def clear_input_error_highlight(self) -> None:
        self.input_panel.clear_error_highlight()

    def adjust_input_font_size(self, delta: int) -> None:
        self._input_font_size = self._update_editor_font_size(
            self.input_edit,
            INPUT_FONT_SIZE_KEY,
            self._input_font_size,
            delta,
            "Input",
        )

    def adjust_output_font_size(self, delta: int) -> None:
        self._output_font_size = self._update_editor_font_size(
            self.output_edit,
            OUTPUT_FONT_SIZE_KEY,
            self._output_font_size,
            delta,
            "Output",
        )

    def set_output_text(
        self,
        text: str,
        *,
        status_text: str = "Ready",
        success: bool = True,
        default_filename: str = "formatted.json",
        parsed_value: object | None = None,
        change_summary: list[str] | None = None,
        repair_warnings: list[str] | None = None,
        risk_level: str | None = None,
    ) -> None:
        self.output_panel.set_output_text(
            text,
            status_text=status_text,
            success=success,
            default_filename=default_filename,
            parsed_value=parsed_value,
        )
        self.output_panel.set_summary(change_summary or [], repair_warnings or [], risk_level)
        self.set_status(status_text)
        self.set_error("")
        self._sync_output_buttons_state()

    def clear_output(self, *, status_text: str = "Ready", error_text: str = "") -> None:
        self.output_panel.clear_output()
        self.clear_input_error_highlight()
        self.set_status(status_text)
        self.set_error(error_text)
        self._sync_output_buttons_state()

    def set_status(self, text: str) -> None:
        self.status_label.setText(text)

    def set_error(self, text: str) -> None:
        self.error_label.setText(text)
        self.status_bar.setStyleSheet("QStatusBar { color: #b00020; }" if text else "")

    def set_processing(self, processing: bool) -> None:
        if processing:
            self.set_status("Processing...")
        elif self.output_panel.has_success:
            self.set_status(self.output_panel.status_text)
        else:
            self.set_status("Ready")

    def set_success_state(
        self,
        output_text: str,
        status_text: str = "Success",
        default_filename: str = "formatted.json",
        parsed_value: object | None = None,
        change_summary: list[str] | None = None,
        repair_warnings: list[str] | None = None,
        risk_level: str | None = None,
    ) -> None:
        self.set_output_text(
            output_text,
            status_text=status_text,
            success=True,
            default_filename=default_filename,
            parsed_value=parsed_value,
            change_summary=change_summary,
            repair_warnings=repair_warnings,
            risk_level=risk_level,
        )

    def set_error_state(self, error_text: str, status_text: str = "Error") -> None:
        self.output_panel.clear_output()
        self.output_panel.set_error_state(status_text=status_text)
        self.set_status(status_text)
        self.set_error(error_text)
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def open_input_file_dialog(self, start_path: str = "") -> None:
        dialog_directory = self._resolve_open_dialog_directory(start_path)
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON Input",
            dialog_directory,
            (
                "JSON and Text Files (*.json *.jsonl *.txt);;"
                "JSON Files (*.json);;"
                "JSON Lines (*.jsonl);;"
                "Text Files (*.txt);;"
                "All Files (*)"
            ),
        )
        if not path:
            return

        self.load_input_file(path)

    def load_input_file(self, path: str) -> bool:
        target_path = Path(path)
        try:
            text = target_path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as exc:
            self._show_warning(f"Failed to open file: {exc}")
            return False

        self.input_panel.set_last_open_path(str(target_path))
        self.set_input_text(text)
        return True

    def _handle_repair_mode_changed(self, _mode: str) -> None:
        if self.get_input_text().strip():
            self._schedule_auto_processing()

    def _resolve_open_dialog_directory(self, start_path: str) -> str:
        if not start_path:
            return ""

        candidate = Path(start_path)
        if candidate.is_dir():
            return str(candidate)
        if candidate.exists():
            return str(candidate.parent)
        if candidate.suffix and candidate.parent != Path("."):
            return str(candidate.parent)
        return str(candidate)

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
            self.output_panel.default_filename,
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
