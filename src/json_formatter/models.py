from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ProcessMode = Literal["format", "repair"]
RepairMode = Literal["strict", "safe", "aggressive"]
StatusLabel = Literal["valid", "repaired", "error"]
RiskLevel = Literal["low", "medium", "high"]
UiLanguage = Literal["ko", "en"]
ThemeMode = Literal["system", "light", "dark"]


@dataclass(slots=True)
class UiMessage:
    code: str
    params: dict[str, str | int] = field(default_factory=dict)


@dataclass(slots=True)
class RepairDiff:
    input_spans: list[tuple[int, int]] = field(default_factory=list)
    output_spans: list[tuple[int, int]] = field(default_factory=list)


@dataclass(slots=True)
class JsonResult:
    success: bool
    mode: ProcessMode
    output_text: str
    error_message: str
    status_label: StatusLabel
    change_summary: list[UiMessage] = field(default_factory=list)
    repair_warnings: list[UiMessage] = field(default_factory=list)
    risk_level: RiskLevel | None = None
    detected_input_kind: str | None = None
    error_line: int | None = None
    error_column: int | None = None
    error_index: int | None = None
    parsed_value: object | None = None
    repair_diff: RepairDiff | None = None
