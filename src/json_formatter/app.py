from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from .models import JsonResult, ProcessMode
from .services import process_json
from .ui import MainWindow


def create_application() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        app.setApplicationName("JSON Viewer & Formatter")
    return app


class JsonFormatterController:
    def __init__(self, window: MainWindow) -> None:
        self.window = window
        self.window.formatRequested.connect(self.handle_format_requested)
        self.window.repairRequested.connect(self.handle_repair_requested)

    def handle_format_requested(self, input_text: str) -> None:
        self._process(input_text, "format")

    def handle_repair_requested(self, input_text: str) -> None:
        self._process(input_text, "repair")

    def _process(self, input_text: str, mode: ProcessMode) -> None:
        self.window.set_processing(True)
        result = process_json(input_text, mode)
        self.window.set_processing(False)
        self._apply_result(result)

    def _apply_result(self, result: JsonResult) -> None:
        if result.success:
            status_text = "Valid JSON" if result.status_label == "valid" else "Repaired JSON"
            default_name = "formatted.json" if result.mode == "format" else "repaired.json"
            self.window.set_success_state(
                result.output_text,
                status_text=status_text,
                default_filename=default_name,
            )
            return

        status_text = "Format failed" if result.mode == "format" else "Repair failed"
        self.window.set_error_state(result.error_message, status_text=status_text)


def main() -> int:
    app = create_application()
    window = MainWindow()
    window.controller = JsonFormatterController(window)
    window.show()
    return app.exec()
