"""Small reusable form widgets."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class ChoiceCombo(QComboBox):
    """A combo of (value, label) choices that can also accept a typed value."""

    def __init__(self, choices: list[tuple[str, str]], editable: bool = False):
        super().__init__()
        self.setEditable(editable)
        self.set_choices(choices)

    def set_choices(self, choices: list[tuple[str, str]]) -> None:
        current = self.value() if self.count() else None
        self.blockSignals(True)
        self.clear()
        for value, label in choices:
            self.addItem(label, value)
        self.blockSignals(False)
        if current is not None:
            self.set_value(current)

    def value(self) -> str:
        i = self.currentIndex()
        if self.isEditable():
            text = self.currentText().strip()
            if i >= 0 and self.itemText(i) == text:
                return self.itemData(i)
            for j in range(self.count()):
                if self.itemText(j) == text:
                    return self.itemData(j)
            return text
        return self.itemData(i) if i >= 0 else ""

    def set_value(self, value: str) -> None:
        i = self.findData(value)
        if i >= 0:
            self.setCurrentIndex(i)
        elif self.isEditable():
            self.setEditText(value)
        elif self.count():
            self.setCurrentIndex(0)


class SecretField(QWidget):
    """Password-style line edit with a show/hide toggle."""

    def __init__(self, placeholder: str = ""):
        super().__init__()
        self.edit = QLineEdit()
        self.edit.setEchoMode(QLineEdit.Password)
        self.edit.setPlaceholderText(placeholder)
        toggle = QPushButton("Show")
        toggle.setCheckable(True)
        toggle.setFixedWidth(64)
        toggle.toggled.connect(lambda on: (
            self.edit.setEchoMode(QLineEdit.Normal if on else QLineEdit.Password),
            toggle.setText("Hide" if on else "Show"),
        ))
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self.edit)
        row.addWidget(toggle)

    def text(self) -> str:
        return self.edit.text().strip()

    def setText(self, value: str) -> None:
        self.edit.setText(value)


class PairTable(QWidget):
    """Editable two-column table (e.g. spoken cue -> text)."""

    def __init__(self, left: str, right: str, add_label: str = "Add"):
        super().__init__()
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels([left, right])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setMinimumHeight(110)
        self.table.setMaximumHeight(170)
        add = QPushButton(add_label)
        remove = QPushButton("Remove")
        add.clicked.connect(self._add)
        remove.clicked.connect(self._remove)
        buttons = QHBoxLayout()
        buttons.addWidget(add)
        buttons.addWidget(remove)
        buttons.addStretch()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.table)
        layout.addLayout(buttons)

    def _add(self) -> None:
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(""))
        self.table.setItem(row, 1, QTableWidgetItem(""))
        self.table.editItem(self.table.item(row, 0))

    def _remove(self) -> None:
        for row in sorted({i.row() for i in self.table.selectedIndexes()}, reverse=True):
            self.table.removeRow(row)

    def set_pairs(self, pairs: dict[str, str]) -> None:
        self.table.setRowCount(0)
        for k, v in pairs.items():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(k))
            self.table.setItem(row, 1, QTableWidgetItem(v))

    def pairs(self) -> dict[str, str]:
        out = {}
        for row in range(self.table.rowCount()):
            k, v = self.table.item(row, 0), self.table.item(row, 1)
            key = k.text().strip() if k else ""
            if key:
                out[key] = v.text() if v else ""
        return out


def hint(text: str) -> QLabel:
    label = QLabel(text)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextBrowserInteraction)
    label.setOpenExternalLinks(True)
    label.setForegroundRole(QPalette.PlaceholderText)
    return label


def heading(text: str) -> QLabel:
    label = QLabel(text)
    font = label.font()
    font.setPointSizeF(font.pointSizeF() * 1.45)
    font.setBold(True)
    label.setFont(font)
    return label
