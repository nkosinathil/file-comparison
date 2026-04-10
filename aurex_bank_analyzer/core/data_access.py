from __future__ import annotations

import math
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def query_scalar(db_path: str, sql: str, params: Tuple[Any, ...] = ()) -> Any:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def query_rows(db_path: str, sql: str, params: Tuple[Any, ...] = ()) -> List[Tuple[Any, ...]]:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()


def get_case_stats(db_path: str) -> Dict[str, Any]:
    if not Path(db_path).exists():
        return {
            "total_transactions": 0,
            "total_debit": 0.0,
            "total_credit": 0.0,
            "min_date": "",
            "max_date": "",
            "files": 0,
        }
    return {
        "total_transactions": int(query_scalar(db_path, "SELECT COUNT(*) FROM fnb_transactions") or 0),
        "total_debit": float(query_scalar(db_path, "SELECT COALESCE(SUM(debit),0) FROM fnb_transactions") or 0.0),
        "total_credit": float(query_scalar(db_path, "SELECT COALESCE(SUM(credit),0) FROM fnb_transactions") or 0.0),
        "min_date": query_scalar(db_path, "SELECT MIN(txn_date) FROM fnb_transactions") or "",
        "max_date": query_scalar(db_path, "SELECT MAX(txn_date) FROM fnb_transactions") or "",
        "files": int(query_scalar(db_path, "SELECT COUNT(DISTINCT source_file) FROM fnb_transactions") or 0),
    }


def categorize_description(description: str) -> str:
    text = (description or "").lower()
    rules = [
        ("Cash Withdrawal", ["atm", "cash withdrawal", "cash@till", "cash withdrawal fee"]),
        ("Transfer / EFT", ["transfer to", "eft", "internet transfer", "online payment", "pay and clear"]),
        ("Card Purchase", ["card purchase", "purchase at", "pos", "visa purchase", "mastercard"]),
        ("Salary / Income", ["salary", "wages", "payroll", "salary from"]),
        ("Debit Order", ["debit order", "stop order"]),
        ("Fees / Charges", ["charge", "fee", "service fee", "bank charge", "commission"]),
        ("Fuel / Travel", ["engen", "shell", "bp ", "uber", "bolt", "kulula", "airways"]),
        ("Retail / Shopping", ["checkers", "shoprite", "pick n pay", "woolworths", "makro", "takealot"]),
        ("Telecoms", ["vodacom", "mtn", "telkom", "cell c"]),
    ]
    for label, needles in rules:
        if any(needle in text for needle in needles):
            return label
    return "Other"


def get_insight_breakdown(db_path: str) -> Dict[str, Any]:
    rows = query_rows(db_path, "SELECT description, debit, credit FROM fnb_transactions ORDER BY txn_date")
    category_totals: Dict[str, float] = defaultdict(float)
    monthly_debit: Dict[str, float] = defaultdict(float)
    top_desc: Counter[str] = Counter()
    for description, debit, credit in rows:
        category = categorize_description(description)
        amount = float(debit or 0 or 0.0)
        if amount <= 0:
            amount = float(credit or 0 or 0.0)
        category_totals[category] += amount
        top_desc[(description or "Unknown")[:60]] += 1
    month_rows = query_rows(
        db_path,
        "SELECT substr(txn_date,1,7) as ym, COALESCE(SUM(debit),0) FROM fnb_transactions GROUP BY ym ORDER BY ym",
    )
    for ym, amt in month_rows:
        monthly_debit[str(ym)] = float(amt or 0.0)
    return {
        "categories": dict(sorted(category_totals.items(), key=lambda x: x[1], reverse=True)),
        "monthly_debit": dict(monthly_debit),
        "top_descriptions": [{"name": name, "count": count} for name, count in top_desc.most_common(10)],
    }


def build_network_data(db_path: str) -> Dict[str, Any]:
    rows = query_rows(db_path, "SELECT txn_date, description, debit, credit, source_file FROM fnb_transactions")
    account_rows = query_rows(db_path, "SELECT DISTINCT source_file FROM fnb_transactions ORDER BY source_file")
    accounts = {r[0]: f"Account {idx+1}" for idx, r in enumerate(account_rows)}

    node_ids: Dict[str, str] = {}
    nodes: List[Dict[str, Any]] = []
    edges_map: Dict[Tuple[str, str], float] = defaultdict(float)

    def ensure_node(key: str, label: str, group: str) -> str:
        if key in node_ids:
            return node_ids[key]
        node_id = f"n{len(node_ids)+1}"
        node_ids[key] = node_id
        nodes.append({"id": node_id, "label": label, "group": group})
        return node_id

    def parse_counterparty(description: str) -> str:
        text = (description or "").strip()
        lowered = text.lower()
        keywords = ["payment to", "transfer to", "paid to", "from", "purchase at", "eft to", "salary from"]
        for keyword in keywords:
            if keyword in lowered:
                idx = lowered.find(keyword)
                candidate = text[idx + len(keyword):].strip(" -:")
                candidate = candidate.split(" ref ")[0].strip()
                candidate = candidate[:35]
                if candidate:
                    return candidate.title()
        return (text[:35] or "Unknown Counterparty").title()

    for source_file, account_label in accounts.items():
        ensure_node(f"account::{source_file}", account_label, "account")

    for txn_date, description, debit, credit, source_file in rows:
        src_id = ensure_node(f"account::{source_file}", accounts.get(source_file, source_file), "account")
        counterparty = parse_counterparty(description)
        cpty_id = ensure_node(f"party::{counterparty}", counterparty, "party")
        amount = float(debit or credit or 0.0)
        if float(debit or 0.0) > 0:
            edge_key = (src_id, cpty_id)
        else:
            edge_key = (cpty_id, src_id)
        edges_map[edge_key] += amount

    edges = [
        {"from": frm, "to": to, "amount": round(amount, 2)}
        for (frm, to), amount in sorted(edges_map.items(), key=lambda x: x[1], reverse=True)[:80]
    ]
    return {"nodes": nodes, "edges": edges}
