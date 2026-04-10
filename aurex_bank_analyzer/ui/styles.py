APP_QSS = """
QMainWindow, QWidget {
    background-color: #0F172A;
    color: #E2E8F0;
    font-family: Segoe UI;
    font-size: 11pt;
}
QTabWidget::pane {
    border: 1px solid #1E293B;
    background: #111827;
    border-radius: 10px;
}
QTabBar::tab {
    background: #111827;
    color: #CBD5E1;
    padding: 10px 18px;
    margin: 4px;
    border-radius: 8px;
}
QTabBar::tab:selected {
    background: #0D9488;
    color: white;
}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QListWidget, QTableWidget {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px;
    color: #E2E8F0;
}
QPushButton {
    background-color: #0D9488;
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 10px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #14B8A6;
}
QPushButton:disabled {
    background-color: #475569;
    color: #CBD5E1;
}
QLabel[role="title"] {
    font-size: 20pt;
    font-weight: 700;
    color: #F59E0B;
}
QLabel[role="subtitle"] {
    font-size: 11pt;
    color: #94A3B8;
}
QGroupBox {
    border: 1px solid #1E293B;
    border-radius: 12px;
    margin-top: 14px;
    padding-top: 14px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px 0 6px;
    color: #F8FAFC;
}
QProgressBar {
    border: 1px solid #334155;
    border-radius: 10px;
    text-align: center;
    background: #111827;
}
QProgressBar::chunk {
    background-color: #F59E0B;
    border-radius: 10px;
}
QHeaderView::section {
    background-color: #1E293B;
    color: #E2E8F0;
    border: none;
    padding: 8px;
}
"""
