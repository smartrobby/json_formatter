from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QFileDialog

from json_formatter.app import JsonFormatterController, create_application
from json_formatter.ui import JsonSyntaxHighlighter
from json_formatter.ui.main_window import MainWindow


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path: Path) -> None:
    app = create_application([])
    previous_org_name = app.organizationName()
    previous_app_name = app.applicationName()
    previous_format = QSettings.defaultFormat()

    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    app.setOrganizationName("json-formatter-tests")
    app.setApplicationName("json-formatter-tests")

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


def test_ui_structure_and_read_only_output(window: MainWindow) -> None:
    assert window.splitter.count() == 2
    assert window.output_edit.isReadOnly() is True
    assert window.input_edit.isReadOnly() is False
    assert window.copy_button.text() == "Copy Output"
    assert window.save_button.text() == "Save Output"
    assert window.auto_mode_label.text() == "Auto format/repair on paste or edit"
    assert isinstance(window.output_highlighter, JsonSyntaxHighlighter)
    assert window.output_highlighter.document() is window.output_edit.document()


def test_buttons_enable_disable_state(window: MainWindow) -> None:
    assert window.copy_button.isEnabled() is False
    assert window.save_button.isEnabled() is False

    window.set_success_state(
        '{\n  "ok": true\n}',
        status_text="Valid JSON",
        default_filename="repaired.json",
    )

    assert window.copy_button.isEnabled() is True
    assert window.save_button.isEnabled() is True
    assert window.get_output_text() == '{\n  "ok": true\n}'

    window.set_error_state("bad input", status_text="Format failed")

    assert window.copy_button.isEnabled() is False
    assert window.save_button.isEnabled() is False
    assert window.error_label.text() == "bad input"


def test_input_change_emits_auto_process_request(window: MainWindow, qtbot) -> None:
    with qtbot.waitSignal(window.autoProcessRequested, timeout=1000) as blocker:
        window.set_input_text('{"x": 1}')

    assert blocker.args == ['{"x": 1}']


def test_shortcuts_are_wired(window: MainWindow) -> None:
    assert window.save_shortcut.key().toString() == "Ctrl+S"


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
    assert window.status_label.text() == f"Input font size: {initial_input_size + 1}pt"


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
    assert window.status_label.text() == f"Output font size: {initial_output_size - 1}pt"


def test_font_sizes_persist_per_pane(window: MainWindow, qtbot) -> None:
    window.adjust_input_font_size(3)
    window.adjust_output_font_size(5)
    qtbot.wait(10)
    window.close()

    restored_window = MainWindow()
    qtbot.addWidget(restored_window)

    assert restored_window.input_edit.font().pointSize() == 13
    assert restored_window.output_edit.font().pointSize() == 15


def test_controller_auto_formats_valid_json(window: MainWindow, qtbot) -> None:
    window.controller = JsonFormatterController(window)
    window.set_input_text('{"a": 1}')

    qtbot.waitUntil(lambda: window.get_output_text() == '{\n  "a": 1\n}', timeout=1000)

    assert window.get_output_text() == '{\n  "a": 1\n}'
    assert window.copy_button.isEnabled() is True
    assert window.save_button.isEnabled() is True
    assert window.status_label.text() == "Valid JSON"


def test_controller_auto_repairs_invalid_json(window: MainWindow, qtbot) -> None:
    window.controller = JsonFormatterController(window)
    window.set_input_text("{'a': 1,}")

    qtbot.waitUntil(lambda: window.get_output_text() == '{\n  "a": 1\n}', timeout=1000)

    assert window.status_label.text() == "Repaired JSON"


def test_save_output_writes_expected_file(window: MainWindow, tmp_path: Path, monkeypatch) -> None:
    output_path = tmp_path / "formatted.json"
    window.set_success_state('{\n  "saved": true\n}', status_text="Valid JSON")

    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *args, **kwargs: (str(output_path), "JSON Files (*.json)"),
    )

    window.save_output_to_file()

    assert output_path.read_text(encoding="utf-8") == '{\n  "saved": true\n}'
