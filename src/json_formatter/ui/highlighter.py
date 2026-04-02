from __future__ import annotations

import re

from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter


class JsonSyntaxHighlighter(QSyntaxHighlighter):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self._brace_format = self._make_format("#5b6572", bold=True)
        self._key_format = self._make_format("#0b5cab", bold=True)
        self._string_format = self._make_format("#227447")
        self._number_format = self._make_format("#b35c00")
        self._literal_format = self._make_format("#a61e4d", bold=True)

        self._string_pattern = re.compile(r'"(?:\\.|[^"\\])*"')
        self._number_pattern = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")
        self._literal_pattern = re.compile(r"\b(?:true|false|null)\b")

    def highlightBlock(self, text: str) -> None:
        for index, char in enumerate(text):
            if char in "{}[]:,":
                self.setFormat(index, 1, self._brace_format)

        for match in self._number_pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self._number_format)

        for match in self._literal_pattern.finditer(text):
            self.setFormat(match.start(), match.end() - match.start(), self._literal_format)

        for match in self._string_pattern.finditer(text):
            start = match.start()
            length = match.end() - match.start()
            suffix = text[match.end() :]
            is_key = bool(re.match(r"\s*:", suffix))
            self.setFormat(start, length, self._key_format if is_key else self._string_format)

    @staticmethod
    def _make_format(color: str, *, bold: bool = False) -> QTextCharFormat:
        text_format = QTextCharFormat()
        text_format.setForeground(QColor(color))
        if bold:
            text_format.setFontWeight(700)
        return text_format
