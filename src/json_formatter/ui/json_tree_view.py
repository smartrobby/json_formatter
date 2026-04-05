from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QHeaderView, QMenu, QTreeWidget, QTreeWidgetItem

from ..models import UiLanguage
from .localization import translate
from .theme import ThemeSpec, get_theme


class JsonTreeView(QTreeWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._language: UiLanguage = "ko"
        self._theme: ThemeSpec = get_theme("system")
        self._search_matches: list[QTreeWidgetItem] = []
        self._search_index = -1
        self.setColumnCount(3)
        self.setUniformRowHeights(True)
        self.header().setSectionResizeMode(QHeaderView.Interactive)
        self._key_column_base_width = self.header().defaultSectionSize()
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.apply_language("ko")
        self.apply_theme(self._theme)

    def apply_language(self, language: UiLanguage) -> None:
        self._language = language
        self.setHeaderLabels(
            [
                translate(language, "tree.key"),
                translate(language, "tree.value"),
                translate(language, "tree.type"),
            ]
        )

    def apply_theme(self, theme: ThemeSpec) -> None:
        self._theme = theme
        self.setStyleSheet(
            (
                "QTreeWidget {"
                f" background: {theme.surface_background};"
                f" color: {theme.foreground};"
                f" border: 1px solid {theme.border};"
                f" selection-background-color: {theme.selection_background};"
                f" selection-color: {theme.selection_foreground};"
                " }"
                "QHeaderView::section {"
                f" background: {theme.surface_alt_background};"
                f" color: {theme.foreground};"
                f" border: 1px solid {theme.border};"
                " padding: 4px 6px; }"
            )
        )

    def set_json_value(self, value: object | None) -> None:
        self.clear()
        self._search_matches = []
        self._search_index = -1
        if value is None:
            return

        self._add_value(self.invisibleRootItem(), value, "$", "root")
        self.expandToDepth(1)
        self._resize_key_column()

    def set_search_term(self, term: str) -> tuple[int, int]:
        normalized = term.strip().lower()
        self.clearSelection()
        self._search_matches = []
        self._search_index = -1

        if not normalized:
            return 0, 0

        for item in self._walk_items():
            haystack = item.data(0, Qt.UserRole + 1) or ""
            if normalized in haystack:
                self._search_matches.append(item)
                self._expand_item_path(item)

        if self._search_matches:
            self._search_index = 0
            self._select_search_item(self._search_matches[0])

        return len(self._search_matches), self._search_index + 1 if self._search_matches else 0

    def select_next_match(self) -> tuple[int, int]:
        if not self._search_matches:
            return 0, 0
        self._search_index = (self._search_index + 1) % len(self._search_matches)
        self._select_search_item(self._search_matches[self._search_index])
        return len(self._search_matches), self._search_index + 1

    def select_previous_match(self) -> tuple[int, int]:
        if not self._search_matches:
            return 0, 0
        self._search_index = (self._search_index - 1) % len(self._search_matches)
        self._select_search_item(self._search_matches[self._search_index])
        return len(self._search_matches), self._search_index + 1

    def selected_json_path(self) -> str:
        item = self.currentItem()
        if item is None:
            return ""
        return item.data(0, Qt.UserRole) or ""

    def expand_subtree(self, item: QTreeWidgetItem | None) -> None:
        if item is None:
            return
        self._set_subtree_expanded(item, True)

    def collapse_subtree(self, item: QTreeWidgetItem | None) -> None:
        if item is None:
            return
        for child_index in range(item.childCount()):
            self._set_subtree_expanded(item.child(child_index), False)
        item.setExpanded(False)

    def _walk_items(self) -> Iterable[QTreeWidgetItem]:
        root = self.invisibleRootItem()
        for index in range(root.childCount()):
            yield from self._walk_subtree(root.child(index))

    def _walk_subtree(self, item: QTreeWidgetItem) -> Iterable[QTreeWidgetItem]:
        yield item
        for index in range(item.childCount()):
            yield from self._walk_subtree(item.child(index))

    def _expand_item_path(self, item: QTreeWidgetItem) -> None:
        current = item
        while current is not None:
            current.setExpanded(True)
            current = current.parent()

    def _set_subtree_expanded(self, item: QTreeWidgetItem, expanded: bool) -> None:
        item.setExpanded(expanded)
        for child_index in range(item.childCount()):
            self._set_subtree_expanded(item.child(child_index), expanded)

    def _select_search_item(self, item: QTreeWidgetItem) -> None:
        self.setCurrentItem(item)
        item.setSelected(True)
        self.scrollToItem(item)

    def _show_context_menu(self, point: QPoint) -> None:
        item = self.itemAt(point)
        if item is None:
            return

        menu = QMenu(self)
        menu.setStyleSheet(
            (
                "QMenu {"
                f" background: {self._theme.surface_background};"
                f" color: {self._theme.foreground};"
                f" border: 1px solid {self._theme.border};"
                " }"
                "QMenu::item:selected {"
                f" background: {self._theme.selection_background};"
                f" color: {self._theme.selection_foreground};"
                " }"
            )
        )

        expand_action = QAction(translate(self._language, "tree.context.expand_subtree"), menu)
        collapse_action = QAction(translate(self._language, "tree.context.collapse_subtree"), menu)
        expand_action.triggered.connect(lambda: self.expand_subtree(item))
        collapse_action.triggered.connect(lambda: self.collapse_subtree(item))
        menu.addAction(expand_action)
        menu.addAction(collapse_action)
        menu.exec(self.viewport().mapToGlobal(point))

    def _add_value(
        self,
        parent: QTreeWidgetItem,
        value: object,
        path: str,
        label: str,
    ) -> None:
        if isinstance(value, dict):
            item = QTreeWidgetItem([label, "", "object"])
            self._set_item_metadata(item, path, label, "", "object")
            parent.addChild(item)
            for key, child_value in value.items():
                child_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                self._add_value(item, child_value, child_path, str(key))
            return

        if isinstance(value, list):
            item = QTreeWidgetItem([label, "", "array"])
            self._set_item_metadata(item, path, label, "", "array")
            parent.addChild(item)
            for index, child_value in enumerate(value):
                child_path = f"{path}[{index}]"
                self._add_value(item, child_value, child_path, f"[{index}]")
            return

        rendered_value = self._render_scalar(value)
        scalar_type = type(value).__name__
        item = QTreeWidgetItem([label, rendered_value, scalar_type])
        self._set_item_metadata(item, path, label, rendered_value, scalar_type)
        parent.addChild(item)

    def _set_item_metadata(
        self,
        item: QTreeWidgetItem,
        path: str,
        label: str,
        value_text: str,
        type_text: str,
    ) -> None:
        item.setData(0, Qt.UserRole, path)
        item.setData(0, Qt.UserRole + 1, " ".join((label, value_text, type_text, path)).lower())

    def _render_scalar(self, value: object) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        return str(value)

    def _resize_key_column(self) -> None:
        self.resizeColumnToContents(0)
        natural_width = max(self.columnWidth(0), self._key_column_base_width)
        self.setColumnWidth(0, natural_width * 3)
