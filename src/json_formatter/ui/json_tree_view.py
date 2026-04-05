from __future__ import annotations

from collections.abc import Iterable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem


class JsonTreeView(QTreeWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setColumnCount(3)
        self.setHeaderLabels(["Key", "Value", "Type"])
        self.setUniformRowHeights(True)

    def set_json_value(self, value: object | None) -> None:
        self.clear()
        if value is None:
            return

        self._add_value(self.invisibleRootItem(), value, "$", "root")
        self.expandToDepth(1)

    def apply_search(self, term: str) -> int:
        normalized = term.strip().lower()
        self.clearSelection()
        if not normalized:
            return 0

        matches: list[QTreeWidgetItem] = []
        for item in self._walk_items():
            haystack = item.data(0, Qt.UserRole + 1) or ""
            if normalized in haystack:
                matches.append(item)
                self._expand_item_path(item)

        if matches:
            first = matches[0]
            first.setSelected(True)
            self.setCurrentItem(first)
            self.scrollToItem(first)

        return len(matches)

    def selected_json_path(self) -> str:
        item = self.currentItem()
        if item is None:
            return ""
        return item.data(0, Qt.UserRole) or ""

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
