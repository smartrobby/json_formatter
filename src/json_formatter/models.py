from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProcessMode = Literal["format", "repair"]
StatusLabel = Literal["valid", "repaired", "error"]


@dataclass(slots=True)
class JsonResult:
    success: bool
    mode: ProcessMode
    output_text: str
    error_message: str
    status_label: StatusLabel
