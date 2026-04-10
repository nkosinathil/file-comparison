from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QThread, Signal, QObject, Slot
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, QTextEdit, QPushButton,
    QListWidget, QListWidgetItem, QPlainTextEdit, QSplitter, QMessageBox
)

from ..core.adapters import get_chat_module
from ..core.data_access import get_case_stats, get_insight_breakdown, build_network_data
from .widgets import DonutChartWidget

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except Exception:  # pragma: no cover
    QWebEngineView = None


class ChatWorker(QObject):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, scripts_dir: Path, db_path: str, question: str):
        super().__init__()
        self.scripts_dir = scripts_dir
        self.db_path = db_path
        self.question = question

    @Slot()
    def run(self) -> None:
        try:
            mod = get_chat_module(self.scripts_dir)
            assistant = mod.FNBStatementChat(self.db_path)
            response = assistant.ask(self.question)
            self.finished.emit(response)
        except Exception as exc:
            self.error.emit(str(exc))


class AnalysisTab(QWidget):
    def __init__(self, scripts_dir: Path, parent=None):
        super().__init__(parent)
        self.scripts_dir = Path(scripts_dir)
        self.current_db_path: str = ""
        self.case_payload = {}

        outer = QVBoxLayout(self)
        title = QLabel("Case Analysis Workspace")
        title.setProperty("role", "title")
        subtitle = QLabel("Review case details, interrogate transactions with AI, inspect network relationships, and view financial insights.")
        subtitle.setProperty("role", "subtitle")
        subtitle.setWordWrap(True)
        outer.addWidget(title)
        outer.addWidget(subtitle)

        split = QSplitter()
        self.case_details = QListWidget()
        self.case_details.setMinimumWidth(260)
        split.addWidget(self.case_details)

        self.tabs = QTabWidget()
        split.addWidget(self.tabs)
        split.setStretchFactor(1, 1)
        outer.addWidget(split, 1)

        # Chat tab
        self.chat_tab = QWidget()
        chat_layout = QVBoxLayout(self.chat_tab)
        self.chat_history = QPlainTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_input = QTextEdit()
        self.chat_input.setFixedHeight(90)
        self.chat_send = QPushButton("Send to AI")
        chat_layout.addWidget(self.chat_history, 1)
        chat_layout.addWidget(self.chat_input)
        chat_layout.addWidget(self.chat_send)
        self.tabs.addTab(self.chat_tab, "AI Chat")

        # Network tab
        self.network_tab = QWidget()
        network_layout = QVBoxLayout(self.network_tab)
        if QWebEngineView is not None:
            self.network_view = QWebEngineView()
        else:
            self.network_view = QTextEdit()
            self.network_view.setReadOnly(True)
        network_layout.addWidget(self.network_view)
        self.tabs.addTab(self.network_tab, "Network")

        # Insights tab
        self.insights_tab = QWidget()
        insights_layout = QVBoxLayout(self.insights_tab)
        self.donut = DonutChartWidget()
        self.insights_text = QPlainTextEdit()
        self.insights_text.setReadOnly(True)
        insights_layout.addWidget(self.donut)
        insights_layout.addWidget(self.insights_text, 1)
        self.tabs.addTab(self.insights_tab, "Insights")

        self.chat_send.clicked.connect(self._send_chat)

    def load_case(self, payload: dict) -> None:
        self.case_payload = payload
        self.current_db_path = payload.get("db_path", "")
        self.chat_history.clear()
        self.chat_input.clear()
        self._refresh_details()
        self._refresh_insights()
        self._refresh_network()

    def _refresh_details(self) -> None:
        self.case_details.clear()
        stats = get_case_stats(self.current_db_path)
        items = {
            "Case Name": self.case_payload.get("case_name", ""),
            "Evidence": self.case_payload.get("evidence_number", ""),
            "Timezone": self.case_payload.get("timezone", ""),
            "Input Folder": self.case_payload.get("input_folder", ""),
            "Database": self.current_db_path,
            "Transactions": str(stats["total_transactions"]),
            "Files": str(stats["files"]),
            "Date Range": f"{stats['min_date']} to {stats['max_date']}".strip(),
            "Case Status": self.case_payload.get("status", ""),
        }
        for key, value in items.items():
            QListWidgetItem(f"{key}: {value}", self.case_details)

    def _refresh_insights(self) -> None:
        if not self.current_db_path:
            return
        data = get_insight_breakdown(self.current_db_path)
        self.donut.set_data(data.get("categories", {}))
        lines = ["Top Transaction Categories:"]
        for name, amount in list(data.get("categories", {}).items())[:10]:
            lines.append(f"- {name}: R {amount:,.2f}")
        lines.append("\nMonthly Debit Trend:")
        for month, amount in data.get("monthly_debit", {}).items():
            lines.append(f"- {month}: R {amount:,.2f}")
        lines.append("\nMost Frequent Descriptions:")
        for item in data.get("top_descriptions", []):
            lines.append(f"- {item['name']} ({item['count']})")
        self.insights_text.setPlainText("\n".join(lines))

    def _refresh_network(self) -> None:
        if not self.current_db_path:
            return
        data = build_network_data(self.current_db_path)
        if QWebEngineView is None:
            lines = ["Network summary:"]
            for node in data["nodes"]:
                lines.append(f"Node: {node['label']} [{node['group']}]")
            for edge in data["edges"][:40]:
                lines.append(f"Edge: {edge['from']} -> {edge['to']} amount R {edge['amount']:,.2f}")
            self.network_view.setPlainText("\n".join(lines))
            return
        html_doc = self._network_html(data)
        self.network_view.setHtml(html_doc)

    def _network_html(self, data: dict) -> str:
        nodes_json = json.dumps(data.get("nodes", []))
        edges_json = json.dumps(data.get("edges", []))
        return f"""
        <html>
        <head>
        <style>
            body {{ background:#0F172A; color:#E2E8F0; font-family:Segoe UI; margin:0; overflow:hidden; }}
            #legend {{ position:absolute; top:12px; left:12px; background:#111827; border:1px solid #334155; border-radius:12px; padding:10px 12px; z-index:2; }}
            .account {{ color:#14B8A6; }} .party {{ color:#F59E0B; }}
            svg {{ width:100vw; height:100vh; }}
            .label {{ fill:#E2E8F0; font-size:12px; }}
        </style>
        </head>
        <body>
        <div id="legend"><b>Network View</b><br><span class="account">● Account</span><br><span class="party">● Counterparty</span></div>
        <svg id="canvas" viewBox="0 0 1200 800"></svg>
        <script>
            const nodes = {nodes_json};
            const edges = {edges_json};
            const svg = document.getElementById('canvas');
            const accountNodes = nodes.filter(n => n.group === 'account');
            const partyNodes = nodes.filter(n => n.group !== 'account');
            const positions = {{}};
            accountNodes.forEach((node, i) => {{
                positions[node.id] = {{ x: 220, y: 120 + i * 180 }};
            }});
            partyNodes.forEach((node, i) => {{
                positions[node.id] = {{ x: 860, y: 80 + (i % 10) * 68 + Math.floor(i / 10) * 12 }};
            }});
            function line(x1,y1,x2,y2,stroke,width) {{
                const el = document.createElementNS('http://www.w3.org/2000/svg','line');
                el.setAttribute('x1',x1); el.setAttribute('y1',y1); el.setAttribute('x2',x2); el.setAttribute('y2',y2);
                el.setAttribute('stroke',stroke); el.setAttribute('stroke-width',width); el.setAttribute('opacity','0.7');
                svg.appendChild(el);
            }}
            function circle(x,y,r,fill) {{
                const el = document.createElementNS('http://www.w3.org/2000/svg','circle');
                el.setAttribute('cx',x); el.setAttribute('cy',y); el.setAttribute('r',r); el.setAttribute('fill',fill);
                svg.appendChild(el);
            }}
            function text(x,y,content) {{
                const el = document.createElementNS('http://www.w3.org/2000/svg','text');
                el.setAttribute('x',x); el.setAttribute('y',y); el.setAttribute('class','label');
                el.textContent = content; svg.appendChild(el);
            }}
            edges.forEach(edge => {{
                const a = positions[edge.from], b = positions[edge.to];
                if (!a || !b) return;
                const w = Math.max(1.5, Math.min(8, edge.amount / 10000));
                line(a.x, a.y, b.x, b.y, '#38BDF8', w);
                text((a.x+b.x)/2 + 4, (a.y+b.y)/2 - 4, 'R ' + Number(edge.amount).toLocaleString(undefined, {{minimumFractionDigits:2, maximumFractionDigits:2}}));
            }});
            nodes.forEach(node => {{
                const p = positions[node.id]; if (!p) return;
                const color = node.group === 'account' ? '#14B8A6' : '#F59E0B';
                const r = node.group === 'account' ? 28 : 16;
                circle(p.x, p.y, r, color);
                text(p.x + r + 10, p.y + 4, node.label);
            }});
        </script>
        </body>
        </html>
        """

    def _send_chat(self) -> None:
        question = self.chat_input.toPlainText().strip()
        if not question:
            return
        if not self.current_db_path:
            QMessageBox.warning(self, "No case loaded", "Load a processed case before using the AI chat.")
            return
        self.chat_history.appendPlainText(f"User: {question}\n")
        self.chat_input.clear()
        self.chat_send.setEnabled(False)
        self.chat_history.appendPlainText("Assistant: Thinking...\n")
        self.chat_thread = QThread(self)
        self.chat_worker = ChatWorker(self.scripts_dir, self.current_db_path, question)
        self.chat_worker.moveToThread(self.chat_thread)
        self.chat_thread.started.connect(self.chat_worker.run)
        self.chat_worker.finished.connect(self._chat_finished)
        self.chat_worker.error.connect(self._chat_error)
        self.chat_worker.finished.connect(self.chat_thread.quit)
        self.chat_worker.error.connect(self.chat_thread.quit)
        self.chat_thread.finished.connect(lambda: self.chat_send.setEnabled(True))
        self.chat_thread.start()

    def _chat_finished(self, response: str) -> None:
        self.chat_history.appendPlainText(f"Assistant: {response}\n")

    def _chat_error(self, message: str) -> None:
        self.chat_history.appendPlainText(
            "Assistant: The AI assistant could not complete the request. "
            f"Reason: {message}. Ensure Ollama is running if you want live model responses.\n"
        )
