from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMimeData, QSettings, QUrl

from json_formatter.app import create_application
from json_formatter.ui.input_panel import InputPanel


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


def test_default_repair_mode_is_safe(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)

    assert panel.current_repair_mode() == "safe"


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


def test_highlight_error_selects_error_line_and_can_be_cleared(tmp_path: Path, qtbot) -> None:
    _set_isolated_settings(tmp_path)
    panel = InputPanel()
    qtbot.addWidget(panel)
    panel.set_text('{\n  "name": "robby",\n  "age": 20,,\n}')

    panel.highlight_error(line=3, column=12, index=30)

    selections = panel.input_edit.extraSelections()
    assert len(selections) == 1
    assert panel.input_edit.textCursor().blockNumber() == 2

    panel.clear_error_highlight()
    assert panel.input_edit.extraSelections() == []
