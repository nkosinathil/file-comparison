from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QPlainTextEdit, QPushButton, QHBoxLayout


class ProgressTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        title = QLabel("Processing Progress")
        title.setProperty("role", "title")
        subtitle = QLabel("The application will parse the selected PDF statements, build the case database, and record progress below.")
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.status_label = QLabel("Waiting to start...")
        self.progress = QProgressBar()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(360)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress)
        layout.addWidget(self.log, 1)

        row = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel")
        self.finish_btn = QPushButton("Finish")
        self.finish_btn.hide()
        row.addWidget(self.cancel_btn)
        row.addWidget(self.finish_btn)
        row.addStretch(1)
        layout.addLayout(row)

    def append_log(self, text: str) -> None:
        self.log.appendPlainText(text)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())
