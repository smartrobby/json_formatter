from __future__ import annotations

from PySide6.QtWidgets import QApplication

from json_formatter.ui.output_panel import OutputPanel
from json_formatter.ui.theme import DARK_THEME


def test_set_output_text_updates_text_tree_and_search_state_without_reparsing(qtbot) -> None:
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

    panel.tree_search_bar.query_edit.setText("alex")

    assert panel.tree_view.selected_json_path() == "$.users[1].name"
    assert "$.users[1].name" in panel.selected_path_label.text()

    panel.copy_selected_path()
    assert QApplication.clipboard().text() == "$.users[1].name"


def test_text_search_and_diff_highlights_can_coexist(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.set_output_text('{\n  "alpha": 1,\n  "beta": 2\n}', parsed_value={"alpha": 1, "beta": 2})
    panel.set_text_diff([(5, 12)])
    panel.text_search_bar.query_edit.setText("beta")

    assert len(panel.output_edit.extraSelections()) >= 2


def test_diff_toggle_hides_diff_but_keeps_search_highlight(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.set_output_text('{\n  "alpha": 1,\n  "beta": 2\n}', parsed_value={"alpha": 1, "beta": 2})
    panel.set_text_diff([(5, 12)])
    panel.text_search_bar.query_edit.setText("beta")

    with_diff = len(panel.output_edit.extraSelections())
    panel.set_diff_highlight_enabled(False)
    without_diff = len(panel.output_edit.extraSelections())

    assert with_diff > without_diff
    assert without_diff >= 1

    panel.set_diff_highlight_enabled(True)
    assert len(panel.output_edit.extraSelections()) == with_diff


def test_tree_expand_and_collapse_buttons_and_subtree_helpers(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.set_tree_value({"users": [{"name": "robby"}, {"name": "alex"}]})

    root_item = panel.tree_view.topLevelItem(0)
    panel.collapse_all_button.click()
    assert root_item.isExpanded() is False

    panel.expand_all_button.click()
    assert root_item.isExpanded() is True

    panel.tree_view.collapse_subtree(root_item)
    assert root_item.isExpanded() is False

    panel.tree_view.expand_subtree(root_item)
    assert root_item.isExpanded() is True


def test_tree_key_column_width_is_tripled_after_populate(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.show()

    base_width = panel.tree_view.header().defaultSectionSize()
    panel.set_tree_value({"veryLongKeyName": {"nestedValue": 1}})

    assert panel.tree_view.columnWidth(0) >= base_width * 3


def test_apply_theme_updates_tree_and_output_styles(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.set_output_text('{"ok": true}', parsed_value={"ok": True})

    panel.apply_theme(DARK_THEME)

    assert DARK_THEME.output_background in panel.output_edit.styleSheet()
    assert DARK_THEME.surface_background in panel.tree_view.styleSheet()


def test_clear_output_resets_tree_search_and_diff(qtbot) -> None:
    panel = OutputPanel()
    qtbot.addWidget(panel)
    panel.set_output_text('{"ok": true}', parsed_value={"ok": True})
    panel.set_text_diff([(2, 6)])
    panel.tree_search_bar.query_edit.setText("ok")
    panel.text_search_bar.query_edit.setText("ok")

    panel.clear_output()

    assert panel.get_text() == ""
    assert panel.tree_view.topLevelItemCount() == 0
    assert panel.text_search_bar.query_edit.text() == ""
    assert panel.tree_search_bar.query_edit.text() == ""
    assert panel.output_edit.extraSelections() == []
