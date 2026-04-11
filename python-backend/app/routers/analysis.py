"""
Analysis Router - Handle data analysis and insights
"""

from collections import defaultdict
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from ..models.database import Case, Transaction, get_db
from ..models.schemas import AnalysisInsights, NetworkData

router = APIRouter()


@router.get("/{case_id}/insights", response_model=AnalysisInsights)
async def get_insights(case_id: str, db: Session = Depends(get_db)):
    """Get financial insights for a case."""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    transactions = db.query(Transaction).filter(Transaction.case_id == case_id).all()
    if not transactions:
        return AnalysisInsights(
            total_transactions=0,
            total_debit=0.0,
            total_credit=0.0,
            date_range={"min": "", "max": ""},
            categories={},
            monthly_trend={},
            top_counterparties=[],
        )

    total_debit = 0.0
    total_credit = 0.0
    categories = defaultdict(float)
    monthly_trend = defaultdict(float)
    counterparties = defaultdict(lambda: {"count": 0, "total": 0.0})
    dates = []

    for txn in transactions:
        amount = float(txn.amount or 0.0)
        if amount < 0:
            total_debit += amount
        else:
            total_credit += amount

        if txn.category:
            categories[txn.category] += abs(amount)

        if txn.transaction_date:
            dates.append(txn.transaction_date)
            month_key = txn.transaction_date.strftime("%Y-%m")
            monthly_trend[month_key] += abs(amount)

        if txn.counterparty:
            cp = counterparties[txn.counterparty]
            cp["count"] += 1
            cp["total"] += abs(amount)

    top_counterparties = sorted(
        (
            {"name": name, "count": stats["count"], "total": round(stats["total"], 2)}
            for name, stats in counterparties.items()
        ),
        key=lambda item: item["total"],
        reverse=True,
    )[:10]

    min_date = min(dates).date().isoformat() if dates else ""
    max_date = max(dates).date().isoformat() if dates else ""

    return AnalysisInsights(
        total_transactions=len(transactions),
        total_debit=round(total_debit, 2),
        total_credit=round(total_credit, 2),
        date_range={"min": min_date, "max": max_date},
        categories={k: round(v, 2) for k, v in categories.items()},
        monthly_trend={k: round(v, 2) for k, v in monthly_trend.items()},
        top_counterparties=top_counterparties,
    )


@router.get("/{case_id}/network", response_model=NetworkData)
async def get_network_data(case_id: str, db: Session = Depends(get_db)):
    """Get network visualization data"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    transactions = db.query(Transaction).filter(Transaction.case_id == case_id).all()
    nodes = {}
    edges = {}

    for txn in transactions:
        if not txn.account_number or not txn.counterparty:
            continue

        account_node_id = f"ACC_{txn.account_number}"
        party_node_id = f"PARTY_{txn.counterparty}"

        nodes[account_node_id] = {
            "id": account_node_id,
            "label": f"Account ***{txn.account_number[-4:]}",
            "group": "account",
        }
        nodes[party_node_id] = {
            "id": party_node_id,
            "label": txn.counterparty,
            "group": "counterparty",
        }

        edge_key = (account_node_id, party_node_id)
        amount = abs(float(txn.amount or 0.0))
        if edge_key not in edges:
            edges[edge_key] = {"from": account_node_id, "to": party_node_id, "amount": 0.0, "count": 0}
        edges[edge_key]["amount"] += amount
        edges[edge_key]["count"] += 1

    return NetworkData(
        nodes=list(nodes.values()),
        edges=[
            {
                "from": edge["from"],
                "to": edge["to"],
                "amount": round(edge["amount"], 2),
                "count": edge["count"],
            }
            for edge in edges.values()
        ],
    )


@router.get("/{case_id}/transactions")
async def get_transactions(
    case_id: str,
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(get_db),
):
    """Get transactions with optional filtering"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    query = db.query(Transaction).filter(Transaction.case_id == case_id)
    if category:
        query = query.filter(Transaction.category == category)

    total = query.count()
    rows = (
        query.order_by(Transaction.transaction_date.desc().nullslast(), Transaction.id.desc())
        .offset(max(skip, 0))
        .limit(min(max(limit, 1), 1000))
        .all()
    )
    return {
        "transactions": [
            {
                "id": row.id,
                "account_number": row.account_number,
                "transaction_date": row.transaction_date.isoformat() if row.transaction_date else None,
                "description": row.description,
                "amount": float(row.amount) if row.amount is not None else None,
                "balance": float(row.balance) if row.balance is not None else None,
                "transaction_type": row.transaction_type,
                "category": row.category,
                "counterparty": row.counterparty,
            }
            for row in rows
        ],
        "total": total,
        "page": (skip // max(limit, 1)) + 1,
    }
