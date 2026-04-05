from __future__ import annotations

from PySide6.QtWidgets import QApplication

from json_formatter.ui.output_panel import OutputPanel


def test_summary_warning_and_risk_widgets_render(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.show()

    panel.set_summary(
        ["Normalized smart quotes", "Combined 2 documents into an array"],
        ["Applied quote heuristic inside a long string"],
        "high",
    )

    assert panel.summary_label.isVisible() is True
    assert panel.warning_label.isVisible() is True
    assert "Normalized smart quotes" in panel.summary_edit.toPlainText()
    assert "Applied quote heuristic" in panel.warning_edit.toPlainText()
    assert panel.risk_badge.text() == "Risk: High"


def test_set_output_text_updates_text_and_tree_without_reparsing(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    parsed_value = {"users": [{"name": "robby"}, {"name": "alex"}]}

    panel.set_output_text(
        '{\n  "users": [\n    {\n      "name": "robby"\n    },\n    {\n      "name": "alex"\n    }\n  ]\n}',
        parsed_value=parsed_value,
    )

    assert panel.get_text().startswith("{\n  \"users\"")
    assert panel.tree_view.topLevelItemCount() == 1
    assert panel.tree_view.topLevelItem(0).text(0) == "root"


def test_tree_search_selects_matching_path_and_copy_path_works(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.set_tree_value({"users": [{"name": "robby"}, {"name": "alex"}]})

    panel.search_input.setText("alex")

    assert panel.search_result_label.text() == "1 matches"
    assert panel.tree_view.selected_json_path() == "$.users[1].name"
    assert panel.selected_path_label.text() == "Selected path: $.users[1].name"

    panel.copy_selected_path()
    assert panel.selected_path_label.text() == "Selected path: $.users[1].name"
    assert panel.tree_view.selected_json_path() == "$.users[1].name"


def test_copy_selected_path_writes_to_clipboard(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.set_tree_value({"users": [{"name": "robby"}]})
    panel.search_input.setText("robby")

    panel.copy_selected_path()

    assert panel.tree_view.selected_json_path() == "$.users[0].name"
    assert panel.selected_path_label.text() == "Selected path: $.users[0].name"
    assert panel.tree_view.selected_json_path() == QApplication.clipboard().text()


def test_clear_output_resets_tree_search_and_summary(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.set_output_text('{"ok": true}', parsed_value={"ok": True})
    panel.set_summary(["Removed trailing comma"], ["Combined documents"], "medium")
    panel.search_input.setText("ok")

    panel.clear_output()

    assert panel.get_text() == ""
    assert panel.tree_view.topLevelItemCount() == 0
    assert panel.search_input.text() == ""
    assert panel.summary_label.isVisible() is False
    assert panel.warning_label.isVisible() is False
    assert panel.risk_badge.isVisible() is False
