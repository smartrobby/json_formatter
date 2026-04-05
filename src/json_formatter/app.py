from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from .models import JsonResult
from .services import process_json
from .ui.localization import translate
from .ui import MainWindow


def create_application(argv: Sequence[str] | None = None) -> QApplication:
    app = QApplication.instance()
    if app is None:
        qt_argv = [sys.argv[0], *list(argv or [])]
        app = QApplication(qt_argv)
    app.setOrganizationName("smartrobby")
    app.setApplicationName("JSON Viewer & Formatter")
    return app


class JsonFormatterController:
    def __init__(self, window: MainWindow) -> None:
        self.window = window
        self.window.autoProcessRequested.connect(self.handle_auto_process_requested)

    def handle_auto_process_requested(self, input_text: str) -> None:
        if not input_text.strip():
            self.window.clear_input_error_highlight()
            self.window.clear_output()
            return

        self.window.set_processing(True)
        result = self._process(input_text)
        self.window.set_processing(False)
        self._apply_result(result)

    def _process(self, input_text: str) -> JsonResult:
        format_result = process_json(input_text, "format")
        if format_result.success:
            return format_result

        repair_result = process_json(
            input_text,
            "repair",
            repair_mode=self.window.current_repair_mode(),
        )
        if repair_result.success:
            return repair_result

        return JsonResult(
            success=False,
            mode="repair",
            output_text="",
            error_message=(
                f"Format failed: {format_result.error_message} | "
                f"Repair failed: {repair_result.error_message}"
            ),
            status_label="error",
            error_line=format_result.error_line,
            error_column=format_result.error_column,
            error_index=format_result.error_index,
        )

    def _apply_result(self, result: JsonResult) -> None:
        if result.success:
            self.window.clear_input_error_highlight()
            status_key = "status.valid_json" if result.status_label == "valid" else "status.repaired_json"
            default_name = "formatted.json" if result.mode == "format" else "repaired.json"
            self.window.set_success_state(
                result.output_text,
                status_key=status_key,
                default_filename=default_name,
                parsed_value=result.parsed_value,
                change_summary=result.change_summary,
                repair_warnings=result.repair_warnings,
                risk_level=result.risk_level,
                repair_diff=result.repair_diff,
            )
            return

        self.window.highlight_input_error(
            line=result.error_line,
            column=result.error_column,
            index=result.error_index,
        )
        self.window.set_error_state(result.error_message, status_key="status.unable_to_process")


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="JSON Viewer & Formatter")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="Run a headless smoke test and exit.",
    )
    parser.add_argument(
        "--smoke-output",
        type=Path,
        help="Write smoke test results to a JSON file.",
    )
    return parser.parse_args(list(argv))


def _write_smoke_report(report_path: Path | None, payload: dict[str, object]) -> None:
    if report_path is None:
        return

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _run_smoke_test(report_path: Path | None) -> int:
    app = create_application([])
    window = MainWindow()
    window.controller = JsonFormatterController(window)

    cases = [
        {
            "name": "format",
            "input": '{"alpha":1,"beta":2}',
            "expected_output": '{\n  "alpha": 1,\n  "beta": 2\n}',
            "expected_status_key": "status.valid_json",
        },
        {
            "name": "repair",
            "input": "{'alpha':1, beta:'two',}",
            "expected_output": '{\n  "alpha": 1,\n  "beta": "two"\n}',
            "expected_status_key": "status.repaired_json",
        },
    ]
    report: dict[str, object] = {"success": True, "cases": []}

    def finish(exit_code: int) -> None:
        _write_smoke_report(report_path, report)
        app.exit(exit_code)

    def check_case(index: int) -> None:
        case = cases[index]
        actual_output = window.get_output_text()
        actual_status = window.status_label.text()
        actual_error = window.error_label.text()
        expected_status = translate(window.current_language(), case["expected_status_key"])
        passed = (
            actual_output == case["expected_output"]
            and actual_status == expected_status
            and actual_error == ""
        )

        case_report = {
            "name": case["name"],
            "passed": passed,
            "status": actual_status,
            "error": actual_error,
            "output": actual_output,
        }
        report_cases = report["cases"]
        assert isinstance(report_cases, list)
        report_cases.append(case_report)

        if not passed:
            report["success"] = False
            finish(1)
            return

        next_index = index + 1
        if next_index >= len(cases):
            finish(0)
            return

        run_case(next_index)

    def run_case(index: int) -> None:
        window.set_input_text(cases[index]["input"])
        delay_ms = window.auto_process_timer.interval() + 250
        QTimer.singleShot(delay_ms, lambda: check_case(index))

    QTimer.singleShot(0, lambda: run_case(0))
    return app.exec()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    if args.smoke_test:
        return _run_smoke_test(args.smoke_output)

    app = create_application([])
    window = MainWindow()
    window.controller = JsonFormatterController(window)
    window.show()
    return app.exec()
