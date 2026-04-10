from __future__ import annotations

import shutil
import sys
from dataclasses import asdict
from pathlib import Path

from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox

from .core.case_manager import CaseManager
from .core.workers import ProcessingWorker
from .ui.styles import APP_QSS
from .ui.welcome import WelcomeTab
from .ui.case_info import CaseInfoTab
from .ui.progress import ProgressTab
from .ui.analysis import AnalysisTab


class AurexWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aurex - Bank Statement Intelligence")
        self.resize(1540, 940)

        base_dir = Path(__file__).resolve().parent
        self.scripts_dir = base_dir / "scripts"
        self.case_manager = CaseManager(base_dir / "cases")
        self.current_case = None
        self.processing_thread = None
        self.processing_worker = None

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.welcome_tab = WelcomeTab()
        self.case_info_tab = CaseInfoTab()
        self.progress_tab = ProgressTab()
        self.analysis_tab = AnalysisTab(self.scripts_dir)

        self.tabs.addTab(self.welcome_tab, "Welcome")
        self.tabs.addTab(self.case_info_tab, "Case Information")
        self.tabs.addTab(self.progress_tab, "Progress")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.setCurrentIndex(0)

        self.welcome_tab.new_case_requested.connect(lambda: self.tabs.setCurrentWidget(self.case_info_tab))
        self.welcome_tab.open_case_requested.connect(self.open_existing_case)
        self.case_info_tab.begin_processing.connect(self.start_case_processing)
        self.progress_tab.cancel_btn.clicked.connect(self.cancel_processing)
        self.progress_tab.finish_btn.clicked.connect(self._open_analysis_from_progress)

        self.refresh_case_listing()

    def refresh_case_listing(self) -> None:
        self.welcome_tab.populate_cases(self.case_manager.list_cases(finished_only=True))

    def start_case_processing(self, payload: dict) -> None:
        missing = [k for k in ["case_name", "evidence_number", "input_folder", "output_folder"] if not payload.get(k)]
        if missing:
            QMessageBox.warning(self, "Missing information", f"Please complete: {', '.join(missing)}")
            return
        input_folder = Path(payload["input_folder"])
        output_folder = Path(payload["output_folder"])
        if not input_folder.exists():
            QMessageBox.warning(self, "Invalid input", "The selected input folder does not exist.")
            return
        output_folder.mkdir(parents=True, exist_ok=True)
        self.current_case = self.case_manager.create_case(**payload)
        self.progress_tab.log.clear()
        self.progress_tab.finish_btn.hide()
        self.progress_tab.cancel_btn.setEnabled(True)
        self.progress_tab.progress.setValue(0)
        self.progress_tab.status_label.setText("Starting processing...")
        self.tabs.setCurrentWidget(self.progress_tab)

        self.processing_thread = QThread(self)
        self.processing_worker = ProcessingWorker(self.scripts_dir, self.current_case.input_folder, self.current_case.db_path)
        self.processing_worker.moveToThread(self.processing_thread)
        self.processing_thread.started.connect(self.processing_worker.run)
        self.processing_worker.log.connect(self.progress_tab.append_log)
        self.processing_worker.progress.connect(self._update_progress)
        self.processing_worker.finished.connect(self._processing_finished)
        self.processing_worker.error.connect(self._processing_error)
        self.processing_worker.finished.connect(self.processing_thread.quit)
        self.processing_worker.error.connect(self.processing_thread.quit)
        self.processing_thread.start()

    def _update_progress(self, current: int, total: int, message: str) -> None:
        self.progress_tab.status_label.setText(message)
        self.progress_tab.progress.setMaximum(max(total, 1))
        self.progress_tab.progress.setValue(current)

    def _processing_finished(self, result: dict) -> None:
        if self.current_case is None:
            return
        stats = result.get("stats", {})
        self.current_case.status = "cancelled" if result.get("cancelled") else "completed"
        self.current_case.processed_files = int(result.get("processed_files", 0))
        self.current_case.total_files = self.progress_tab.progress.maximum()
        self.current_case.total_transactions = int(stats.get("total_transactions", 0))
        min_date = stats.get("min_date", "")
        max_date = stats.get("max_date", "")
        self.current_case.date_range = f"{min_date} to {max_date}".strip()
        self.case_manager.save_case(self.current_case)
        self.progress_tab.progress.setValue(self.progress_tab.progress.maximum())
        self.progress_tab.status_label.setText("Processing completed" if not result.get("cancelled") else "Processing cancelled")
        self.progress_tab.finish_btn.setVisible(not result.get("cancelled"))
        self.progress_tab.cancel_btn.setEnabled(False)
        self.refresh_case_listing()
        if not result.get("cancelled"):
            self.analysis_tab.load_case(asdict(self.current_case))

    def _processing_error(self, message: str) -> None:
        if self.current_case is not None:
            self.current_case.status = "error"
            self.case_manager.save_case(self.current_case)
            self.refresh_case_listing()
        QMessageBox.critical(self, "Processing error", message)
        self.progress_tab.append_log(f"Fatal error: {message}")
        self.progress_tab.cancel_btn.setEnabled(False)

    def cancel_processing(self) -> None:
        if self.processing_worker is not None:
            self.processing_worker.cancel()
            self.progress_tab.append_log("Cancellation requested...")

    def _open_analysis_from_progress(self) -> None:
        if self.current_case is None:
            return
        self.analysis_tab.load_case(asdict(self.current_case))
        self.tabs.setCurrentWidget(self.analysis_tab)

    def open_existing_case(self, case_id: str) -> None:
        record = self.case_manager.load_case(case_id)
        if record is None:
            QMessageBox.warning(self, "Case not found", "The selected case could not be loaded.")
            return
        self.current_case = record
        self.analysis_tab.load_case(asdict(record))
        self.tabs.setCurrentWidget(self.analysis_tab)


def ensure_scripts_present(base_dir: Path) -> None:
    scripts_dir = base_dir / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    root = base_dir.parent
    for name in ["fnb_statement_to_sqlite.py", "fnb_chat_assistant-v2.py", "account_analyzer.py"]:
        src = root / name
        dst = scripts_dir / name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(APP_QSS)
    base_dir = Path(__file__).resolve().parent
    ensure_scripts_present(base_dir)
    window = AurexWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
