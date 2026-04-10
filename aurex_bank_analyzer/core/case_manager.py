from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional


@dataclass
class CaseRecord:
    case_id: str
    case_name: str
    evidence_number: str
    case_description: str
    timezone: str
    input_folder: str
    output_folder: str
    db_path: str
    status: str = "new"
    created_at: str = ""
    updated_at: str = ""
    total_files: int = 0
    processed_files: int = 0
    total_transactions: int = 0
    date_range: str = ""


class CaseManager:
    def __init__(self, cases_root: Path):
        self.cases_root = Path(cases_root)
        self.cases_root.mkdir(parents=True, exist_ok=True)

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _case_dir(self, case_id: str) -> Path:
        return self.cases_root / case_id

    def create_case(
        self,
        case_name: str,
        evidence_number: str,
        case_description: str,
        timezone: str,
        input_folder: str,
        output_folder: str,
    ) -> CaseRecord:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(ch if ch.isalnum() else "_" for ch in case_name).strip("_") or "CASE"
        case_id = f"{safe_name}_{stamp}"
        case_dir = self._case_dir(case_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(case_dir / "fnb_statements.db")
        record = CaseRecord(
            case_id=case_id,
            case_name=case_name,
            evidence_number=evidence_number,
            case_description=case_description,
            timezone=timezone,
            input_folder=input_folder,
            output_folder=output_folder,
            db_path=db_path,
            status="created",
            created_at=self._now(),
            updated_at=self._now(),
        )
        self.save_case(record)
        return record

    def save_case(self, record: CaseRecord) -> None:
        case_dir = self._case_dir(record.case_id)
        case_dir.mkdir(parents=True, exist_ok=True)
        record.updated_at = self._now()
        with open(case_dir / "case.json", "w", encoding="utf-8") as fh:
            json.dump(asdict(record), fh, indent=2, ensure_ascii=False)

    def load_case(self, case_id: str) -> Optional[CaseRecord]:
        path = self._case_dir(case_id) / "case.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return CaseRecord(**data)

    def list_cases(self, finished_only: bool = False) -> List[CaseRecord]:
        records: List[CaseRecord] = []
        for case_json in sorted(self.cases_root.glob("*/case.json"), reverse=True):
            try:
                with open(case_json, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                record = CaseRecord(**data)
                if finished_only and record.status != "completed":
                    continue
                records.append(record)
            except Exception:
                continue
        return records
