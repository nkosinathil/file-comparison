from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QHeaderView
)

from ..core.case_manager import CaseRecord


class WelcomeTab(QWidget):
    new_case_requested = Signal()
    open_case_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)

        title = QLabel("Aurex Bank Statement Intelligence")
        title.setProperty("role", "title")
        subtitle = QLabel(
            "A premium forensic-style workspace for ingesting PDF bank statements, building case-ready SQLite data, "
            "interrogating transactions with AI, mapping account relationships, and surfacing visual insights."
        )
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        btn_row = QHBoxLayout()
        self.new_case_btn = QPushButton("Create New Case")
        self.open_selected_btn = QPushButton("Open Selected Completed Case")
        self.open_selected_btn.setEnabled(False)
        btn_row.addWidget(self.new_case_btn)
        btn_row.addWidget(self.open_selected_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.case_table = QTableWidget(0, 6)
        self.case_table.setHorizontalHeaderLabels([
            "Case Name", "Evidence", "Status", "Transactions", "Date Range", "Updated"
        ])
        self.case_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.case_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.case_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.case_table, 1)

        self.new_case_btn.clicked.connect(self.new_case_requested.emit)
        self.open_selected_btn.clicked.connect(self._emit_selected_case)
        self.case_table.itemSelectionChanged.connect(self._selection_changed)
        self.case_table.itemDoubleClicked.connect(lambda *_: self._emit_selected_case())

    def populate_cases(self, cases: list[CaseRecord]) -> None:
        self.case_table.setRowCount(0)
        for record in cases:
            row = self.case_table.rowCount()
            self.case_table.insertRow(row)
            values = [
                record.case_name,
                record.evidence_number,
                record.status,
                str(record.total_transactions),
                record.date_range,
                record.updated_at,
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, record.case_id)
                self.case_table.setItem(row, col, item)
        self.open_selected_btn.setEnabled(False)

    def _selection_changed(self) -> None:
        selected = self.case_table.selectedItems()
        self.open_selected_btn.setEnabled(bool(selected))

    def _emit_selected_case(self) -> None:
        row = self.case_table.currentRow()
        if row < 0:
            return
        item = self.case_table.item(row, 0)
        if item is None:
            return
        case_id = item.data(Qt.UserRole)
        if case_id:
            self.open_case_requested.emit(case_id)
