from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QTextEdit,
    QComboBox, QPushButton, QFileDialog, QHBoxLayout
)


class CaseInfoTab(QWidget):
    begin_processing = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Case Information")
        title.setProperty("role", "title")
        subtitle = QLabel("Create a new case and point the application to the folder containing PDF bank statements.")
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        form = QFormLayout()
        self.case_name = QLineEdit()
        self.evidence_number = QLineEdit()
        self.case_description = QTextEdit()
        self.case_description.setFixedHeight(100)
        self.timezone = QComboBox()
        self.timezone.addItems(["Africa/Johannesburg (GMT+2)", "UTC", "GMT+1", "GMT+3"])
        self.input_folder = QLineEdit()
        self.output_folder = QLineEdit()

        input_row = QHBoxLayout()
        input_row.addWidget(self.input_folder)
        self.browse_input = QPushButton("Browse")
        input_row.addWidget(self.browse_input)

        output_row = QHBoxLayout()
        output_row.addWidget(self.output_folder)
        self.browse_output = QPushButton("Browse")
        output_row.addWidget(self.browse_output)

        form.addRow("Case Name", self.case_name)
        form.addRow("Evidence Number", self.evidence_number)
        form.addRow("Case Description", self.case_description)
        form.addRow("Timezone", self.timezone)
        form.addRow("Input Folder", input_row)
        form.addRow("Output Folder", output_row)
        layout.addLayout(form)

        self.begin_btn = QPushButton("Begin Processing")
        layout.addWidget(self.begin_btn)
        layout.addStretch(1)

        self.browse_input.clicked.connect(self._pick_input)
        self.browse_output.clicked.connect(self._pick_output)
        self.begin_btn.clicked.connect(self._emit_payload)

    def _pick_input(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Input Folder")
        if folder:
            self.input_folder.setText(folder)

    def _pick_output(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_folder.setText(folder)

    def _emit_payload(self) -> None:
        payload = {
            "case_name": self.case_name.text().strip(),
            "evidence_number": self.evidence_number.text().strip(),
            "case_description": self.case_description.toPlainText().strip(),
            "timezone": self.timezone.currentText(),
            "input_folder": self.input_folder.text().strip(),
            "output_folder": self.output_folder.text().strip(),
        }
        self.begin_processing.emit(payload)
