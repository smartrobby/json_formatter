from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from ..models import ThemeMode


@dataclass(frozen=True, slots=True)
class ThemeSpec:
    requested_mode: ThemeMode
    resolved_mode: str
    window_background: str
    surface_background: str
    surface_alt_background: str
    foreground: str
    muted_foreground: str
    border: str
    accent: str
    syntax_brace: str
    syntax_key: str
    syntax_string: str
    syntax_number: str
    syntax_literal: str
    parse_error_background: str
    parse_error_foreground: str
    diff_background: str
    diff_foreground: str
    search_background: str
    search_foreground: str
    search_active_background: str
    search_active_foreground: str
    selection_background: str
    selection_foreground: str
    warning_background: str
    warning_foreground: str
    input_background: str
    output_background: str


LIGHT_THEME = ThemeSpec(
    requested_mode="light",
    resolved_mode="light",
    window_background="#f4f6fb",
    surface_background="#ffffff",
    surface_alt_background="#fbfcfe",
    foreground="#142033",
    muted_foreground="#5b6572",
    border="#d6dbe5",
    accent="#0b5cab",
    syntax_brace="#5b6572",
    syntax_key="#0b5cab",
    syntax_string="#227447",
    syntax_number="#b35c00",
    syntax_literal="#a61e4d",
    parse_error_background="#ffe7e8",
    parse_error_foreground="#6b1117",
    diff_background="#0b5cab",
    diff_foreground="#ffffff",
    search_background="#fff2b3",
    search_foreground="#473800",
    search_active_background="#ffbe0b",
    search_active_foreground="#2e2200",
    selection_background="#dbeafe",
    selection_foreground="#0f172a",
    warning_background="#fef3c7",
    warning_foreground="#7c2d12",
    input_background="#ffffff",
    output_background="#fbfcfe",
)

DARK_THEME = ThemeSpec(
    requested_mode="dark",
    resolved_mode="dark",
    window_background="#0f1726",
    surface_background="#172133",
    surface_alt_background="#111827",
    foreground="#e5edf7",
    muted_foreground="#93a4bd",
    border="#2a3850",
    accent="#67b4ff",
    syntax_brace="#93a4bd",
    syntax_key="#67b4ff",
    syntax_string="#7fd69a",
    syntax_number="#ffb86b",
    syntax_literal="#ff6b9a",
    parse_error_background="#58252a",
    parse_error_foreground="#ffe1e4",
    diff_background="#67b4ff",
    diff_foreground="#08111f",
    search_background="#5d4a00",
    search_foreground="#fff3bf",
    search_active_background="#f4b400",
    search_active_foreground="#1f1400",
    selection_background="#1f3b63",
    selection_foreground="#f8fbff",
    warning_background="#4f2f10",
    warning_foreground="#ffe0c2",
    input_background="#172133",
    output_background="#111827",
)


def detect_system_theme(app: QApplication | None = None) -> str:
    palette = (app or QApplication.instance()).palette() if (app or QApplication.instance()) else QPalette()
    base_color = palette.color(QPalette.Window)
    return "dark" if base_color.lightness() < 128 else "light"


def get_theme(mode: ThemeMode, app: QApplication | None = None) -> ThemeSpec:
    if mode == "light":
        return LIGHT_THEME
    if mode == "dark":
        return DARK_THEME

    resolved_mode = detect_system_theme(app)
    source = DARK_THEME if resolved_mode == "dark" else LIGHT_THEME
    return ThemeSpec(
        requested_mode="system",
        resolved_mode=resolved_mode,
        window_background=source.window_background,
        surface_background=source.surface_background,
        surface_alt_background=source.surface_alt_background,
        foreground=source.foreground,
        muted_foreground=source.muted_foreground,
        border=source.border,
        accent=source.accent,
        syntax_brace=source.syntax_brace,
        syntax_key=source.syntax_key,
        syntax_string=source.syntax_string,
        syntax_number=source.syntax_number,
        syntax_literal=source.syntax_literal,
        parse_error_background=source.parse_error_background,
        parse_error_foreground=source.parse_error_foreground,
        diff_background=source.diff_background,
        diff_foreground=source.diff_foreground,
        search_background=source.search_background,
        search_foreground=source.search_foreground,
        search_active_background=source.search_active_background,
        search_active_foreground=source.search_active_foreground,
        selection_background=source.selection_background,
        selection_foreground=source.selection_foreground,
        warning_background=source.warning_background,
        warning_foreground=source.warning_foreground,
        input_background=source.input_background,
        output_background=source.output_background,
    )


def qcolor(hex_value: str) -> QColor:
    return QColor(hex_value)
