from __future__ import annotations

from math import cos, sin, pi
from typing import Dict

from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import QWidget


class DonutChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: Dict[str, float] = {}
        self.palette = [
            QColor("#14B8A6"),
            QColor("#F59E0B"),
            QColor("#38BDF8"),
            QColor("#A78BFA"),
            QColor("#F87171"),
            QColor("#10B981"),
        ]
        self.setMinimumHeight(320)

    def set_data(self, data: Dict[str, float]) -> None:
        self.data = data or {}
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(20, 20, -20, -20)
        radius = min(rect.width(), rect.height()) * 0.35
        center_x = rect.center().x() - 80
        center_y = rect.center().y()
        total = sum(max(v, 0) for v in self.data.values())

        if total <= 0:
            painter.setPen(QColor("#94A3B8"))
            painter.drawText(rect, Qt.AlignCenter, "No insight data available")
            return

        pie_rect = QRectF(center_x - radius, center_y - radius, radius * 2, radius * 2)
        start_angle = 90 * 16
        items = list(self.data.items())[:6]
        for idx, (label, value) in enumerate(items):
            span = int(-360 * 16 * (value / total))
            painter.setBrush(self.palette[idx % len(self.palette)])
            painter.setPen(QPen(QColor("#0F172A"), 2))
            painter.drawPie(pie_rect, start_angle, span)
            start_angle += span

        painter.setBrush(QColor("#0F172A"))
        painter.setPen(Qt.NoPen)
        inner = radius * 0.55
        painter.drawEllipse(QRectF(center_x - inner, center_y - inner, inner * 2, inner * 2))
        painter.setPen(QColor("#E2E8F0"))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(center_x - inner, center_y - 20, inner * 2, 40), Qt.AlignCenter, f"R {total:,.2f}")

        legend_x = int(center_x + radius + 30)
        legend_y = int(center_y - 100)
        painter.setFont(QFont("Segoe UI", 9))
        for idx, (label, value) in enumerate(items):
            painter.setBrush(self.palette[idx % len(self.palette)])
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(legend_x, legend_y + idx * 34, 18, 18, 4, 4)
            painter.setPen(QColor("#E2E8F0"))
            painter.drawText(legend_x + 28, legend_y + 14 + idx * 34, f"{label}: R {value:,.2f}")
