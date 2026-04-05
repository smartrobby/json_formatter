from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QFileDialog

from json_formatter.app import JsonFormatterController, create_application
from json_formatter.models import RepairDiff, UiMessage
from json_formatter.ui import JsonSyntaxHighlighter
from json_formatter.ui.localization import translate
from json_formatter.ui.main_window import MainWindow


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path) -> None:
    app = create_application([])
    previous_org_name = app.organizationName()
    previous_app_name = app.applicationName()
    previous_format = QSettings.defaultFormat()

    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    app.setOrganizationName("json-formatter-ui-tests")
    app.setApplicationName("json-formatter-ui-tests")

    settings = QSettings()
    settings.clear()
    settings.sync()

    yield

    settings = QSettings()
    settings.clear()
    settings.sync()
    app.setOrganizationName(previous_org_name)
    app.setApplicationName(previous_app_name)
    QSettings.setDefaultFormat(previous_format)


@pytest.fixture
def window(qtbot) -> MainWindow:
    create_application([])
    widget = MainWindow()
    qtbot.addWidget(widget)
    return widget


def test_ui_structure_defaults_and_read_only_output(window: MainWindow) -> None:
    assert window.splitter.count() == 2
    assert window.output_edit.isReadOnly() is True
    assert window.input_edit.isReadOnly() is False
    assert window.copy_button.text() == "Copy Output"
    assert window.save_button.text() == "Save Output"
    assert window.auto_mode_label.text() == translate("ko", "toolbar.auto_mode")
    assert isinstance(window.output_highlighter, JsonSyntaxHighlighter)
    assert window.output_highlighter.document() is window.output_edit.document()
    assert window.current_repair_mode() == "safe"
    assert window.current_language() == "ko"
    assert window.current_theme_mode() == "system"
    assert window.language_combo.currentData() == "ko"
    assert window.theme_combo.currentData() == "system"
    assert window.diff_highlight_button.isChecked() is False


def test_buttons_enable_disable_state(window: MainWindow) -> None:
    assert window.copy_button.isEnabled() is False
    assert window.save_button.isEnabled() is False

    window.set_success_state(
        '{\n  "ok": true\n}',
        status_key="status.valid_json",
        default_filename="repaired.json",
        parsed_value={"ok": True},
    )

    assert window.copy_button.isEnabled() is True
    assert window.save_button.isEnabled() is True
    assert window.get_output_text() == '{\n  "ok": true\n}'
    assert window.output_panel.tree_view.topLevelItemCount() == 1

    window.set_error_state("bad input", status_key="status.unable_to_process")

    assert window.copy_button.isEnabled() is False
    assert window.save_button.isEnabled() is False
    assert window.error_label.text() == "bad input"
    assert window.get_output_text() == ""


def test_input_change_emits_auto_process_request(window: MainWindow, qtbot) -> None:
    with qtbot.waitSignal(window.autoProcessRequested, timeout=1000) as blocker:
        window.set_input_text('{"x": 1}')

    assert blocker.args == ['{"x": 1}']


def test_shortcuts_are_wired(window: MainWindow) -> None:
    assert window.save_shortcut.key().toString() == "Ctrl+S"
    assert window.find_shortcut.key().toString() == "Ctrl+F"
    assert window.input_panel.open_shortcut.key().toString() == "Ctrl+O"


def test_ctrl_wheel_adjusts_input_font_size_independently(window: MainWindow) -> None:
    initial_input_size = window.input_edit.font().pointSize()
    initial_output_size = window.output_edit.font().pointSize()

    zoom_in_event = QWheelEvent(
        QPointF(20, 20),
        QPointF(20, 20),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.NoButton,
        Qt.ControlModifier,
        Qt.ScrollUpdate,
        False,
    )
    window.input_edit.wheelEvent(zoom_in_event)

    assert window.input_edit.font().pointSize() == initial_input_size + 1
    assert window.output_edit.font().pointSize() == initial_output_size
    assert window.status_label.text() == translate("ko", "status.input_font_size", size=initial_input_size + 1)


def test_ctrl_wheel_adjusts_output_font_size_independently(window: MainWindow) -> None:
    initial_input_size = window.input_edit.font().pointSize()
    initial_output_size = window.output_edit.font().pointSize()

    zoom_out_event = QWheelEvent(
        QPointF(20, 20),
        QPointF(20, 20),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.NoButton,
        Qt.ControlModifier,
        Qt.ScrollUpdate,
        False,
    )
    window.output_edit.wheelEvent(zoom_out_event)

    assert window.input_edit.font().pointSize() == initial_input_size
    assert window.output_edit.font().pointSize() == initial_output_size - 1
    assert window.status_label.text() == translate("ko", "status.output_font_size", size=initial_output_size - 1)


def test_font_sizes_persist_per_pane(window: MainWindow, qtbot) -> None:
    window.adjust_input_font_size(3)
    window.adjust_output_font_size(5)
    qtbot.wait(10)
    window.close()

    restored_window = MainWindow()
    qtbot.addWidget(restored_window)

    assert restored_window.input_edit.font().pointSize() == 13
    assert restored_window.output_edit.font().pointSize() == 15


def test_language_and_theme_persist_and_rerender_summary(window: MainWindow, qtbot) -> None:
    window.set_success_state(
        '{\n  "alpha": 1\n}',
        status_key="status.repaired_json",
        parsed_value={"alpha": 1},
        change_summary=[UiMessage("removed_utf8_bom")],
        repair_warnings=[UiMessage("combined_top_level_documents", {"count": 2})],
        risk_level="medium",
    )

    window.language_combo.setCurrentIndex(window.language_combo.findData("en"))
    window.theme_combo.setCurrentIndex(window.theme_combo.findData("dark"))
    qtbot.wait(10)
    window.close()

    restored_window = MainWindow()
    qtbot.addWidget(restored_window)

    assert restored_window.current_language() == "en"
    assert restored_window.current_theme_mode() == "dark"
    assert window.input_panel.summary_edit.toPlainText() == "- Removed UTF-8 BOM."
    assert "single JSON array" in window.input_panel.warning_edit.toPlainText()


def test_diff_highlight_toggle_hides_and_restores_repair_diff(window: MainWindow) -> None:
    window.set_input_text('{"a":1,}')
    window.set_success_state(
        '{\n  "a": 1\n}',
        status_key="status.repaired_json",
        parsed_value={"a": 1},
        repair_diff=RepairDiff(input_spans=[(6, 7)], output_spans=[(1, 4)]),
    )

    assert window.input_edit.extraSelections() == []
    assert window.output_edit.extraSelections() == []

    window.diff_highlight_button.click()

    assert window.diff_highlight_button.isChecked() is True
    assert len(window.input_edit.extraSelections()) >= 1
    assert len(window.output_edit.extraSelections()) >= 1

    window.diff_highlight_button.click()

    assert window.diff_highlight_button.isChecked() is False
    assert window.input_edit.extraSelections() == []
    assert window.output_edit.extraSelections() == []


def test_diff_toggle_state_survives_reprocessing_but_not_new_window(window: MainWindow, qtbot) -> None:
    window.controller = JsonFormatterController(window)

    window.set_input_text('data: {"users":[{"name":"robby"}]}\n\ndata: {"users":[{"name":"alex"}]}\n\n')
    qtbot.waitUntil(lambda: window.status_label.text() == translate("ko", "status.repaired_json"), timeout=1000)

    assert window.diff_highlight_button.isChecked() is False
    assert window.output_edit.extraSelections() == []

    window.diff_highlight_button.click()
    assert window.diff_highlight_button.isChecked() is True

    window.set_input_text('data: {"users":[{"name":"sam"}]}\n\ndata: {"users":[{"name":"jane"}]}\n\n')
    qtbot.waitUntil(lambda: window.status_label.text() == translate("ko", "status.repaired_json"), timeout=1000)
    assert len(window.input_edit.extraSelections()) >= 1
    assert len(window.output_edit.extraSelections()) >= 1

    restored_window = MainWindow()
    qtbot.addWidget(restored_window)
    assert restored_window.diff_highlight_button.isChecked() is False


def test_controller_auto_formats_valid_json_and_clears_error_highlight(window: MainWindow, qtbot) -> None:
    window.controller = JsonFormatterController(window)
    window.highlight_input_error(line=1, column=1, index=0)

    window.set_input_text('{"a": 1}')

    qtbot.waitUntil(lambda: window.get_output_text() == '{\n  "a": 1\n}', timeout=1000)

    assert window.status_label.text() == translate("ko", "status.valid_json")
    assert window.error_label.text() == ""
    assert window.input_panel._error_index is None
    assert window.input_panel.summary_label.isVisible() is False
    assert window.output_panel.tree_view.topLevelItemCount() == 1
    assert window.output_edit.extraSelections() == []


def test_controller_auto_repairs_invalid_json_and_populates_input_metadata(window: MainWindow, qtbot) -> None:
    window.controller = JsonFormatterController(window)
    window.set_input_text('data: {"users":[{"name":"robby"}]}\n\ndata: {"users":[{"name":"alex"}]}\n\n')

    qtbot.waitUntil(lambda: window.status_label.text() == translate("ko", "status.repaired_json"), timeout=1000)

    assert window.get_output_text().startswith("[\n  {\n    \"users\"")
    assert "payload" in window.input_panel.summary_edit.toPlainText()
    assert "JSON array" in window.input_panel.warning_edit.toPlainText()
    assert window.input_panel.risk_badge.isHidden() is False
    assert window.output_panel.tree_view.topLevelItemCount() == 1
    assert window.input_edit.extraSelections() == []
    assert window.output_edit.extraSelections() == []
    assert window.output_panel.summary_label.isVisible() is False
    assert window.output_panel.warning_label.isVisible() is False
    assert window.output_panel.risk_badge.isVisible() is False


def test_ctrl_f_routes_to_focused_view_search_bars(window: MainWindow, qtbot) -> None:
    window.show()
    qtbot.wait(20)

    window.input_edit.setFocus()
    qtbot.wait(20)
    window.show_search_for_focused_view()
    assert window.input_panel.search_bar.isHidden() is False

    window.output_panel.tab_widget.setCurrentIndex(0)
    window.output_edit.setFocus()
    qtbot.wait(20)
    window.show_search_for_focused_view()
    assert window.output_panel.text_search_bar.isHidden() is False

    window.output_panel.tab_widget.setCurrentIndex(1)
    window.output_panel.tree_view.setFocus()
    qtbot.wait(20)
    window.show_search_for_focused_view()
    assert window.output_panel.tree_search_bar.isHidden() is False


def test_strict_repair_mode_failure_highlights_input_error(window: MainWindow, qtbot) -> None:
    window.controller = JsonFormatterController(window)
    window.input_panel.set_repair_mode("strict")
    window.set_input_text('{"a":1}\n{"b":2}')

    qtbot.waitUntil(lambda: "Strict repair mode" in window.error_label.text(), timeout=1000)

    assert window.status_label.text() == translate("ko", "status.unable_to_process")
    assert len(window.input_edit.extraSelections()) == 1
    assert window.input_edit.textCursor().blockNumber() == 1
    assert window.get_output_text() == ""


def test_repair_mode_change_reprocesses_and_replaces_error_with_diff_highlights(window: MainWindow, qtbot) -> None:
    window.controller = JsonFormatterController(window)
    window.input_panel.set_repair_mode("strict")
    window.set_input_text('{"a":1}\n{"b":2}')
    qtbot.waitUntil(lambda: "Strict repair mode" in window.error_label.text(), timeout=1000)

    assert len(window.input_edit.extraSelections()) == 1

    window.input_panel.set_repair_mode("safe")

    qtbot.waitUntil(lambda: window.status_label.text() == translate("ko", "status.repaired_json"), timeout=1000)

    assert window.input_panel._error_index is None
    assert window.input_panel.risk_badge.isHidden() is False
    assert window.input_edit.extraSelections() == []
    assert window.output_edit.extraSelections() == []

    window.diff_highlight_button.click()
    assert len(window.input_edit.extraSelections()) >= 1
    assert len(window.output_edit.extraSelections()) >= 1


def test_open_file_dialog_loads_input_and_processes(window: MainWindow, qtbot, tmp_path: Path, monkeypatch) -> None:
    sample_path = tmp_path / "sample.json"
    sample_path.write_text('{"loaded": true}', encoding="utf-8")
    window.controller = JsonFormatterController(window)

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (str(sample_path), "JSON Files (*.json)"),
    )

    window.input_panel.open_button.click()

    qtbot.waitUntil(lambda: window.get_input_text() == '{"loaded": true}', timeout=1000)
    qtbot.waitUntil(lambda: window.status_label.text() == translate("ko", "status.valid_json"), timeout=1000)

    assert window.get_output_text() == '{\n  "loaded": true\n}'
    assert window.input_panel.last_open_path() == str(sample_path)


def test_save_output_writes_expected_file(window: MainWindow, tmp_path: Path, monkeypatch) -> None:
    output_path = tmp_path / "formatted.json"
    window.set_success_state(
        '{\n  "saved": true\n}',
        status_key="status.valid_json",
        parsed_value={"saved": True},
    )

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output_path), "JSON Files (*.json)"),
    )

    window.save_output_to_file()

    assert output_path.read_text(encoding="utf-8") == '{\n  "saved": true\n}'
