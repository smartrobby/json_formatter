from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog

from json_formatter.app import JsonFormatterController
from json_formatter.ui.main_window import MainWindow


@pytest.fixture
def window(qtbot) -> MainWindow:
    widget = MainWindow()
    qtbot.addWidget(widget)
    return widget


def test_ui_structure_and_read_only_output(window: MainWindow) -> None:
    assert window.splitter.count() == 2
    assert window.output_edit.isReadOnly() is True
    assert window.input_edit.isReadOnly() is False
    assert window.format_button.text() == "Format"
    assert window.repair_button.text() == "Repair"


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


def test_button_clicks_emit_requested_signals(window: MainWindow, qtbot) -> None:
    captured = {"format": "", "repair": ""}
    window.formatRequested.connect(lambda text: captured.__setitem__("format", text))
    window.repairRequested.connect(lambda text: captured.__setitem__("repair", text))

    window.set_input_text('{"x": 1}')
    qtbot.mouseClick(window.format_button, Qt.LeftButton)
    qtbot.mouseClick(window.repair_button, Qt.LeftButton)

    assert captured["format"] == '{"x": 1}'
    assert captured["repair"] == '{"x": 1}'


def test_shortcuts_are_wired(window: MainWindow) -> None:
    assert window.format_shortcut.key().toString() == "Ctrl+Return"
    assert window.repair_shortcut.key().toString() == "Ctrl+Shift+Return"
    assert window.save_shortcut.key().toString() == "Ctrl+S"


def test_controller_updates_window_state(window: MainWindow) -> None:
    controller = JsonFormatterController(window)
    window.set_input_text('{"a": 1}')

    window.formatRequested.emit(window.get_input_text())

    assert window.get_output_text() == '{\n  "a": 1\n}'
    assert window.copy_button.isEnabled() is True
    assert window.save_button.isEnabled() is True
    assert window.status_label.text() == "Valid JSON"


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
