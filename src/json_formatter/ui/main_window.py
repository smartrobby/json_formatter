from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSettings, QTimer, Qt, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
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

from ..models import RepairDiff, ThemeMode, UiLanguage, UiMessage
from .input_panel import InputPanel
from .localization import translate
from .output_panel import OutputPanel
from .theme import ThemeSpec, get_theme

DEFAULT_EDITOR_FONT_SIZE = 10
MIN_EDITOR_FONT_SIZE = 8
MAX_EDITOR_FONT_SIZE = 28
INPUT_FONT_SIZE_KEY = "ui/font_size/input"
OUTPUT_FONT_SIZE_KEY = "ui/font_size/output"
LANGUAGE_KEY = "ui/language"
THEME_KEY = "ui/theme"


class MainWindow(QMainWindow):
    autoProcessRequested = Signal(str)
    copyRequested = Signal(str)
    saveRequested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.controller = None
        self._settings = self._create_settings()
        self._language: UiLanguage = self._load_language()
        self._theme_mode: ThemeMode = self._load_theme_mode()
        self._theme: ThemeSpec = get_theme(self._theme_mode, QApplication.instance())
        self._input_font_size = self._load_font_size(INPUT_FONT_SIZE_KEY, DEFAULT_EDITOR_FONT_SIZE)
        self._output_font_size = self._load_font_size(OUTPUT_FONT_SIZE_KEY, DEFAULT_EDITOR_FONT_SIZE)
        self._diff_highlight_enabled = False
        self._last_repair_diff: RepairDiff | None = None
        self._last_repair_status_label: str | None = None
        self._status_key = "status.ready"
        self._status_params: dict[str, str | int] = {}
        self._raw_status_text = ""
        self._error_text = ""

        self.auto_process_timer = QTimer(self)
        self.auto_process_timer.setSingleShot(True)
        self.auto_process_timer.setInterval(200)

        self._build_ui()
        self._wire_actions()
        self._apply_language()
        self._apply_theme()
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

        self.auto_mode_label = QLabel(toolbar)
        self.language_label = QLabel(toolbar)
        self.language_combo = QComboBox(toolbar)
        self.theme_label = QLabel(toolbar)
        self.theme_combo = QComboBox(toolbar)
        self.diff_highlight_button = QPushButton(toolbar)
        self.diff_highlight_button.setCheckable(True)
        self.diff_highlight_button.setChecked(False)
        self.copy_button = QPushButton(toolbar)
        self.save_button = QPushButton(toolbar)

        toolbar_layout.addWidget(self.auto_mode_label)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.language_label)
        toolbar_layout.addWidget(self.language_combo)
        toolbar_layout.addWidget(self.theme_label)
        toolbar_layout.addWidget(self.theme_combo)
        toolbar_layout.addWidget(self.diff_highlight_button)
        toolbar_layout.addWidget(self.copy_button)
        toolbar_layout.addWidget(self.save_button)

        self.splitter = QSplitter(Qt.Horizontal, central)
        self.splitter.setChildrenCollapsible(False)

        self.input_panel = InputPanel(self.splitter)
        self.output_panel = OutputPanel(self.splitter)

        self.input_edit = self.input_panel.input_edit
        self.output_edit = self.output_panel.output_edit
        self.output_highlighter = self.output_panel.output_highlighter

        root_layout.addWidget(toolbar)
        root_layout.addWidget(self.splitter, 1)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_label = QLabel(self.status_bar)
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
        self.language_combo.currentIndexChanged.connect(self._handle_language_changed)
        self.theme_combo.currentIndexChanged.connect(self._handle_theme_changed)
        self.diff_highlight_button.toggled.connect(self._handle_diff_highlight_toggled)

        self.input_edit.textChanged.connect(self._schedule_auto_processing)
        self.auto_process_timer.timeout.connect(self._emit_auto_process_requested)
        self.input_edit.fontZoomRequested.connect(self.adjust_input_font_size)
        self.output_edit.fontZoomRequested.connect(self.adjust_output_font_size)
        self.input_panel.openFileRequested.connect(self.open_input_file_dialog)
        self.input_panel.fileDropped.connect(self.load_input_file)
        self.input_panel.repairModeChanged.connect(self._handle_repair_mode_changed)

        self.save_shortcut = QShortcut(QKeySequence.Save, self)
        self.save_shortcut.activated.connect(self.save_output_to_file)
        self.find_shortcut = QShortcut(QKeySequence.Find, self)
        self.find_shortcut.activated.connect(self.show_search_for_focused_view)

    def _create_settings(self) -> QSettings:
        app = QApplication.instance()
        if app is not None:
            if not app.organizationName():
                app.setOrganizationName("smartrobby")
            if not app.applicationName():
                app.setApplicationName("JSON Viewer & Formatter")
        return QSettings()

    def _load_language(self) -> UiLanguage:
        raw_value = str(self._settings.value(LANGUAGE_KEY, "ko"))
        return raw_value if raw_value in {"ko", "en"} else "ko"

    def _load_theme_mode(self) -> ThemeMode:
        raw_value = str(self._settings.value(THEME_KEY, "system"))
        return raw_value if raw_value in {"system", "light", "dark"} else "system"

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
        status_key: str,
    ) -> int:
        new_size = self._clamp_font_size(current_size + delta)
        if new_size == current_size:
            return current_size

        self._apply_editor_font_size(editor, new_size)
        self._settings.setValue(key, new_size)
        self._settings.sync()
        self.set_status_key(status_key, size=new_size)
        return new_size

    def _apply_default_state(self) -> None:
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.input_panel.set_diff_highlight_enabled(self._diff_highlight_enabled)
        self.output_panel.set_diff_highlight_enabled(self._diff_highlight_enabled)
        self.input_panel.set_summary([], [], None)
        self.set_status_key("status.ready")
        self.set_error("")

    def _populate_language_combo(self) -> None:
        current = self._language
        options = [
            ("ko", translate(self._language, "combo.language.ko")),
            ("en", translate(self._language, "combo.language.en")),
        ]
        self.language_combo.blockSignals(True)
        self.language_combo.clear()
        for value, label in options:
            self.language_combo.addItem(label, value)
        self.language_combo.setCurrentIndex(max(0, self.language_combo.findData(current)))
        self.language_combo.blockSignals(False)

    def _populate_theme_combo(self) -> None:
        current = self._theme_mode
        options = [
            ("system", translate(self._language, "combo.theme.system")),
            ("light", translate(self._language, "combo.theme.light")),
            ("dark", translate(self._language, "combo.theme.dark")),
        ]
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        for value, label in options:
            self.theme_combo.addItem(label, value)
        self.theme_combo.setCurrentIndex(max(0, self.theme_combo.findData(current)))
        self.theme_combo.blockSignals(False)

    def _apply_language(self) -> None:
        self.setWindowTitle(translate(self._language, "app.title"))
        self.auto_mode_label.setText(translate(self._language, "toolbar.auto_mode"))
        self.language_label.setText(translate(self._language, "toolbar.language"))
        self.theme_label.setText(translate(self._language, "toolbar.theme"))
        self.diff_highlight_button.setText(translate(self._language, "button.diff_highlight"))
        self.copy_button.setText(translate(self._language, "button.copy_output"))
        self.save_button.setText(translate(self._language, "button.save_output"))
        self._populate_language_combo()
        self._populate_theme_combo()
        self.input_panel.apply_language(self._language)
        self.output_panel.apply_language(self._language)
        self._render_status()

    def _apply_theme(self) -> None:
        self._theme = get_theme(self._theme_mode, QApplication.instance())
        central = self.centralWidget()
        if central is not None:
            central.setStyleSheet(
                (
                    "QWidget {"
                    f" background: {self._theme.window_background};"
                    f" color: {self._theme.foreground};"
                    " }"
                    "QFrame {"
                    f" background: {self._theme.window_background};"
                    " }"
                    "QComboBox, QPushButton {"
                    f" background: {self._theme.surface_background};"
                    f" color: {self._theme.foreground};"
                    f" border: 1px solid {self._theme.border};"
                    " padding: 4px 8px; }"
                )
            )
        self.status_bar.setStyleSheet(
            (
                "QStatusBar {"
                f" background: {self._theme.surface_background};"
                f" color: {self._theme.foreground};"
                f" border-top: 1px solid {self._theme.border};"
                " }"
            )
        )
        self.input_panel.apply_theme(self._theme)
        self.output_panel.apply_theme(self._theme)
        self._render_status()

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
        enabled = self.output_panel.has_success and bool(self.output_panel.text)
        self.copy_button.setEnabled(enabled)
        self.save_button.setEnabled(enabled)

    def _mark_output_stale(self) -> None:
        self.output_panel.mark_stale()
        self.input_panel.set_summary([], [], None)
        self.output_panel.set_tree_value(None)
        self.output_panel.clear_text_diff()
        self.input_panel.clear_diff_spans()
        self._last_repair_diff = None
        self._last_repair_status_label = None
        self.set_status_key("status.updating")
        self.set_error("")
        self._sync_output_buttons_state()

    def _render_status(self) -> None:
        if self._status_key:
            self.status_label.setText(translate(self._language, self._status_key, **self._status_params))
            return
        self.status_label.setText(self._raw_status_text)

    def set_input_text(self, text: str) -> None:
        self.input_panel.set_text(text)

    def get_input_text(self) -> str:
        return self.input_panel.get_text()

    def get_output_text(self) -> str:
        return self.output_panel.get_text()

    def current_repair_mode(self) -> str:
        return self.input_panel.current_repair_mode()

    def current_language(self) -> UiLanguage:
        return self._language

    def current_theme_mode(self) -> ThemeMode:
        return self._theme_mode

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

    def set_input_diff_spans(self, spans: list[tuple[int, int]]) -> None:
        self.input_panel.set_diff_spans(spans)

    def clear_input_diff_spans(self) -> None:
        self.input_panel.clear_diff_spans()

    def adjust_input_font_size(self, delta: int) -> None:
        self._input_font_size = self._update_editor_font_size(
            self.input_edit,
            INPUT_FONT_SIZE_KEY,
            self._input_font_size,
            delta,
            "status.input_font_size",
        )

    def adjust_output_font_size(self, delta: int) -> None:
        self._output_font_size = self._update_editor_font_size(
            self.output_edit,
            OUTPUT_FONT_SIZE_KEY,
            self._output_font_size,
            delta,
            "status.output_font_size",
        )

    def set_output_text(
        self,
        text: str,
        *,
        status_key: str = "status.ready",
        success: bool = True,
        default_filename: str = "formatted.json",
        parsed_value: object | None = None,
        change_summary: list[UiMessage] | None = None,
        repair_warnings: list[UiMessage] | None = None,
        risk_level: str | None = None,
        repair_diff: RepairDiff | None = None,
    ) -> None:
        self.output_panel.set_output_text(
            text,
            status_text=status_key,
            success=success,
            default_filename=default_filename,
            parsed_value=parsed_value,
        )
        self.input_panel.set_summary(change_summary or [], repair_warnings or [], risk_level)
        if status_key == "status.repaired_json" and repair_diff is not None:
            self._last_repair_diff = repair_diff
            self._last_repair_status_label = "repaired"
        else:
            self._last_repair_diff = None
            self._last_repair_status_label = "valid"
        self.output_panel.set_text_diff(repair_diff.output_spans if repair_diff else [])
        self.input_panel.set_diff_spans(repair_diff.input_spans if repair_diff else [])
        self.input_panel.set_diff_highlight_enabled(self._diff_highlight_enabled)
        self.output_panel.set_diff_highlight_enabled(self._diff_highlight_enabled)
        self.set_status_key(status_key)
        self.set_error("")
        self._sync_output_buttons_state()

    def clear_output(self, *, status_key: str = "status.ready", error_text: str = "") -> None:
        self.output_panel.clear_output()
        self.input_panel.set_summary([], [], None)
        self.clear_input_error_highlight()
        self.clear_input_diff_spans()
        self._last_repair_diff = None
        self._last_repair_status_label = None
        self.set_status_key(status_key)
        self.set_error(error_text)
        self._sync_output_buttons_state()

    def set_status_key(self, key: str, **params: str | int) -> None:
        self._status_key = key
        self._status_params = params
        self._raw_status_text = ""
        self._render_status()

    def set_status(self, text: str) -> None:
        self._status_key = ""
        self._status_params = {}
        self._raw_status_text = text
        self.status_label.setText(text)

    def set_error(self, text: str) -> None:
        self._error_text = text
        self.error_label.setText(text)
        if text:
            self.error_label.setStyleSheet(f"QLabel {{ color: {self._theme.parse_error_foreground}; }}")
        else:
            self.error_label.setStyleSheet("")

    def set_processing(self, processing: bool) -> None:
        if processing:
            self.set_status_key("status.processing")
        elif self.output_panel.has_success:
            self._render_status()
        else:
            self.set_status_key("status.ready")

    def set_success_state(
        self,
        output_text: str,
        status_key: str = "status.valid_json",
        default_filename: str = "formatted.json",
        parsed_value: object | None = None,
        change_summary: list[UiMessage] | None = None,
        repair_warnings: list[UiMessage] | None = None,
        risk_level: str | None = None,
        repair_diff: RepairDiff | None = None,
    ) -> None:
        self.set_output_text(
            output_text,
            status_key=status_key,
            success=True,
            default_filename=default_filename,
            parsed_value=parsed_value,
            change_summary=change_summary,
            repair_warnings=repair_warnings,
            risk_level=risk_level,
            repair_diff=repair_diff,
        )

    def set_error_state(self, error_text: str, status_key: str = "status.unable_to_process") -> None:
        self.output_panel.clear_output()
        self.output_panel.set_error_state(status_text=status_key)
        self.input_panel.set_summary([], [], None)
        self.clear_input_diff_spans()
        self._last_repair_diff = None
        self._last_repair_status_label = None
        self.set_status_key(status_key)
        self.set_error(error_text)
        self.copy_button.setEnabled(False)
        self.save_button.setEnabled(False)

    def open_input_file_dialog(self, start_path: str = "") -> None:
        from PySide6.QtWidgets import QFileDialog

        dialog_directory = self._resolve_open_dialog_directory(start_path)
        path, _ = QFileDialog.getOpenFileName(
            self,
            translate(self._language, "dialog.open_json_input"),
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
            self._show_warning(translate(self._language, "error.open_file_failed", error=str(exc)))
            return False

        self.input_panel.set_last_open_path(str(target_path))
        self.set_input_text(text)
        return True

    def _handle_repair_mode_changed(self, _mode: str) -> None:
        if self.get_input_text().strip():
            self._schedule_auto_processing()

    def _handle_language_changed(self, _index: int) -> None:
        language = self.language_combo.currentData()
        if not isinstance(language, str) or language not in {"ko", "en"} or language == self._language:
            return
        self._language = language
        self._settings.setValue(LANGUAGE_KEY, language)
        self._settings.sync()
        self._apply_language()

    def _handle_theme_changed(self, _index: int) -> None:
        mode = self.theme_combo.currentData()
        if not isinstance(mode, str) or mode not in {"system", "light", "dark"} or mode == self._theme_mode:
            return
        self._theme_mode = mode
        self._settings.setValue(THEME_KEY, mode)
        self._settings.sync()
        self._apply_theme()

    def _handle_diff_highlight_toggled(self, checked: bool) -> None:
        self._diff_highlight_enabled = checked
        self.input_panel.set_diff_highlight_enabled(checked)
        self.output_panel.set_diff_highlight_enabled(checked)
        if checked and self._last_repair_status_label == "repaired" and self._last_repair_diff is not None:
            self.input_panel.set_diff_spans(self._last_repair_diff.input_spans)
            self.output_panel.set_text_diff(self._last_repair_diff.output_spans)

    def show_search_for_focused_view(self) -> None:
        focus_widget = QApplication.focusWidget()
        if focus_widget is None:
            self.input_panel.show_search()
            return

        if focus_widget is self.input_edit or self.input_edit.isAncestorOf(focus_widget):
            self.input_panel.show_search()
            return

        if focus_widget is self.output_edit or self.output_edit.isAncestorOf(focus_widget):
            self.output_panel.show_text_search()
            return

        if focus_widget is self.output_panel.tree_view or self.output_panel.tree_view.isAncestorOf(focus_widget):
            self.output_panel.show_tree_search()
            return

        if self.output_panel.tab_widget.currentIndex() == 1:
            self.output_panel.show_tree_search()
            return

        self.output_panel.show_text_search()

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
            self._show_warning(translate(self._language, "error.no_output_copy"))
            return
        QApplication.clipboard().setText(text)
        self.copyRequested.emit(text)
        self.set_status_key("status.copied_output")

    def save_output_to_file(self) -> None:
        from PySide6.QtWidgets import QFileDialog

        text = self.get_output_text()
        if not text:
            self._show_warning(translate(self._language, "error.no_output_save"))
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            translate(self._language, "dialog.save_json_output"),
            self.output_panel.default_filename,
            "JSON Files (*.json);;All Files (*)",
        )
        if not path:
            return

        try:
            with open(path, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
        except OSError as exc:
            self._show_warning(translate(self._language, "error.save_file_failed", error=str(exc)))
            return

        self.saveRequested.emit(path)
        self.set_status_key("status.saved_to", path=path)

    def _show_warning(self, message: str) -> None:
        QMessageBox.warning(self, translate(self._language, "dialog.app_name"), message)
