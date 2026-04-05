from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData, QSettings, QUrl

from json_formatter.app import create_application
from json_formatter.models import UiMessage
from json_formatter.ui.input_panel import InputPanel
from json_formatter.ui.theme import DARK_THEME


class DummyDropEvent:
    def __init__(self, mime_data: QMimeData) -> None:
        self._mime_data = mime_data
        self.accepted = False
        self.ignored = False

    def mimeData(self) -> QMimeData:
        return self._mime_data

    def acceptProposedAction(self) -> None:
        self.accepted = True

    def ignore(self) -> None:
        self.ignored = True


def _make_file_mime_data(path: Path) -> QMimeData:
    mime_data = QMimeData()
    mime_data.setUrls([QUrl.fromLocalFile(str(path))])
    return mime_data


def _make_text_mime_data(text: str) -> QMimeData:
    mime_data = QMimeData()
    mime_data.setText(text)
    return mime_data


def _set_isolated_settings(tmp_path: Path) -> None:
    app = create_application([])
    QSettings.setDefaultFormat(QSettings.IniFormat)
    QSettings.setPath(QSettings.IniFormat, QSettings.UserScope, str(tmp_path))
    app.setOrganizationName("json-formatter-input-panel-tests")
    app.setApplicationName("json-formatter-input-panel-tests")
    settings = QSettings()
    settings.clear()
    settings.sync()


def test_default_repair_mode_is_safe_and_language_is_korean(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)

    assert panel.current_repair_mode() == "safe"
    assert panel.title_label.text() == "Raw JSON Input"
    assert panel.search_button.text()


def test_summary_warning_and_risk_widgets_render_in_input_panel(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    panel.show()

    panel.set_summary(
        [
            UiMessage("normalized_smart_double_quotes"),
            UiMessage("combined_top_level_documents", {"count": 2}),
        ],
        [UiMessage("escaped_suspicious_quotes")],
        "high",
    )

    assert panel.summary_label.isVisible() is True
    assert panel.warning_label.isVisible() is True
    assert "smart double quotes" in panel.summary_edit.toPlainText()
    assert "quote" in panel.warning_edit.toPlainText()
    assert panel.risk_badge.isHidden() is False


def test_repair_mode_persists_between_instances(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)

    panel.set_repair_mode("aggressive")
    panel.close()

    restored_panel = InputPanel()
    qtbot.addWidget(restored_panel)

    assert restored_panel.current_repair_mode() == "aggressive"


def test_open_button_emits_signal_with_last_path(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    sample_path = str(tmp_path / "sample.json")
    panel.set_last_open_path(sample_path)

    with qtbot.waitSignal(panel.openFileRequested, timeout=1000) as blocker:
        panel.open_button.click()

    assert blocker.args == [sample_path]


def test_open_shortcut_emits_signal_with_last_path(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    sample_path = str(tmp_path / "shortcut.json")
    panel.set_last_open_path(sample_path)

    with qtbot.waitSignal(panel.openFileRequested, timeout=1000) as blocker:
        panel.open_shortcut.activated.emit()

    assert blocker.args == [sample_path]


def test_drag_enter_and_drop_emit_file_path_and_persist_last_path(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    dropped_file = tmp_path / "dropped.json"
    dropped_file.write_text('{"ok": true}', encoding="utf-8")

    drag_event = DummyDropEvent(_make_file_mime_data(dropped_file))
    panel.dragEnterEvent(drag_event)
    assert drag_event.accepted is True

    drop_event = DummyDropEvent(_make_file_mime_data(dropped_file))
    with qtbot.waitSignal(panel.fileDropped, timeout=1000) as blocker:
        panel.dropEvent(drop_event)

    assert drop_event.accepted is True
    assert blocker.args == [str(dropped_file)]
    assert panel.last_open_path() == str(dropped_file)


def test_drag_enter_rejects_non_file_data(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)

    drag_event = DummyDropEvent(_make_text_mime_data("not-a-file"))
    panel.dragEnterEvent(drag_event)

    assert drag_event.ignored is True


def test_highlight_error_diff_and_search_can_be_cleared(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    panel.set_text('{\n  "name": "robby",\n  "age": 20,,\n}')

    panel.highlight_error(line=3, column=12, index=30)
    panel.set_diff_spans([(5, 11)])
    panel.show_search()
    panel.search_bar.query_edit.setText("robby")

    selections = panel.input_edit.extraSelections()
    assert len(selections) >= 3
    assert panel.input_edit.textCursor().selectedText() == "robby"

    panel.clear_error_highlight()
    panel.clear_diff_spans()
    panel.search_bar.close_bar()
    assert panel.input_edit.extraSelections() == []


def test_diff_toggle_hides_diff_but_keeps_search_and_error(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    panel.set_text('{\n  "name": "robby",\n  "age": 20,,\n}')
    panel.highlight_error(line=3, column=12, index=30)
    panel.set_diff_spans([(5, 11)])
    panel.show_search()
    panel.search_bar.query_edit.setText("robby")

    with_diff = len(panel.input_edit.extraSelections())
    panel.set_diff_highlight_enabled(False)
    without_diff = len(panel.input_edit.extraSelections())

    assert with_diff > without_diff
    assert without_diff >= 2


def test_apply_theme_updates_editor_styles_search_bar_and_summary_widgets(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    panel.set_summary([UiMessage("removed_utf8_bom")], [UiMessage("combined_top_level_documents", {"count": 2})], "medium")

    panel.apply_theme(DARK_THEME)

    assert DARK_THEME.input_background in panel.input_edit.styleSheet()
    assert DARK_THEME.surface_background in panel.search_bar.styleSheet()
    assert DARK_THEME.surface_alt_background in panel.summary_edit.styleSheet()
    assert panel.risk_badge.isHidden() is False
