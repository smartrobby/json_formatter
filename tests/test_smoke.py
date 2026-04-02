from __future__ import annotations

from PySide6.QtWidgets import QApplication

from json_formatter.app import create_application
from json_formatter.ui.main_window import MainWindow


def test_main_window_can_be_instantiated_headless(qtbot) -> None:
    app = create_application()
    assert isinstance(app, QApplication)

    window = MainWindow()
    qtbot.addWidget(window)

    assert window.windowTitle() == "JSON Viewer & Formatter"
    assert window.isVisible() is False
    assert window.output_edit.isReadOnly() is True
