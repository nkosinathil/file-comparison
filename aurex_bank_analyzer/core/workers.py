from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, Signal, Slot

from .adapters import get_statement_module
from .data_access import get_case_stats


class ProcessingWorker(QObject):
    progress = Signal(int, int, str)
    log = Signal(str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, scripts_dir: Path, input_folder: str, db_path: str):
        super().__init__()
        self.scripts_dir = Path(scripts_dir)
        self.input_folder = input_folder
        self.db_path = db_path
        self._cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            mod = get_statement_module(self.scripts_dir)
            pdf_files = sorted(Path(self.input_folder).glob("*.pdf"))
            if not pdf_files:
                raise FileNotFoundError("No PDF bank statements were found in the selected input folder.")
            mod.create_database(self.db_path)
            total = len(pdf_files)
            self.log.emit(f"Detected {total} PDF statement(s).")
            processed = 0
            for index, pdf_path in enumerate(pdf_files, start=1):
                if self._cancelled:
                    self.log.emit("Processing cancelled by user.")
                    self.finished.emit({"cancelled": True, "stats": get_case_stats(self.db_path)})
                    return
                self.progress.emit(index - 1, total, f"Processing {pdf_path.name}")
                self.log.emit(f"[{index}/{total}] Processing {pdf_path.name}")
                try:
                    statement_date, txns, file_hash = mod.parse_pdf_statement(str(pdf_path))
                    if getattr(mod, "is_file_processed", None) and mod.is_file_processed(self.db_path, file_hash):
                        self.log.emit(f"Skipped already processed file: {pdf_path.name}")
                    else:
                        mod.save_transactions_to_db(self.db_path, txns)
                        mod.mark_file_processed(self.db_path, pdf_path.name, file_hash, statement_date, len(txns))
                        processed += 1
                        self.log.emit(f"Saved {len(txns)} transaction(s) from {pdf_path.name}")
                except Exception as exc:
                    self.log.emit(f"Error on {pdf_path.name}: {exc}")
            self.progress.emit(total, total, "Processing complete")
            stats = get_case_stats(self.db_path)
            self.finished.emit({"cancelled": False, "processed_files": processed, "stats": stats})
        except Exception as exc:
            self.error.emit(str(exc))

    def cancel(self) -> None:
        self._cancelled = True
