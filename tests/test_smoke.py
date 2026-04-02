from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtWidgets import QApplication

from json_formatter.app import _run_smoke_test, create_application
from json_formatter.ui.main_window import MainWindow


def test_main_window_can_be_instantiated_headless(qtbot) -> None:
    app = create_application()
    assert isinstance(app, QApplication)

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "JSON Viewer & Formatter"
    assert window.isVisible() is False
    assert window.output_edit.isReadOnly() is True


def test_smoke_runner_writes_success_report(tmp_path: Path) -> None:
    report_path = tmp_path / "smoke-report.json"

    exit_code = _run_smoke_test(report_path)

    assert exit_code == 0
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    assert payload["success"] is True
    assert len(payload["cases"]) == 2
