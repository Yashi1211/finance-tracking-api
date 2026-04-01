from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction, TransactionType
from app.schemas import TransactionCreate, TransactionUpdate


def _filter_criteria(
    *,
    date_from: date | None,
    date_to: date | None,
    category: str | None,
    transaction_type: TransactionType | None,
):
    crit = []
    if date_from is not None:
        crit.append(Transaction.date >= date_from)
    if date_to is not None:
        crit.append(Transaction.date <= date_to)
    if category is not None and category.strip():
        crit.append(Transaction.category == category.strip())
    if transaction_type is not None:
        crit.append(Transaction.type == transaction_type)
    return crit


def _apply_filters(
    stmt,
    *,
    date_from: date | None,
    date_to: date | None,
    category: str | None,
    transaction_type: TransactionType | None,
):
    crit = _filter_criteria(
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    if crit:
        stmt = stmt.where(*crit)
    return stmt


def create_transaction(db: Session, data: TransactionCreate) -> Transaction:
    row = Transaction(
        amount=float(data.amount),
        type=TransactionType(data.type.value),
        category=data.category,
        date=data.date,
        note=data.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_transaction(db: Session, transaction_id: int) -> Transaction | None:
    return db.get(Transaction, transaction_id)


def count_transactions(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    transaction_type: TransactionType | None = None,
) -> int:
    stmt = select(func.count()).select_from(Transaction)
    stmt = _apply_filters(
        stmt,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    return int(db.scalar(stmt) or 0)


def list_transactions(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    transaction_type: TransactionType | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Transaction]:
    stmt = select(Transaction).order_by(Transaction.date.desc(), Transaction.id.desc())
    stmt = _apply_filters(
        stmt,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    stmt = stmt.offset(skip).limit(min(limit, 500))
    return list(db.scalars(stmt).all())


def update_transaction(
    db: Session, transaction_id: int, data: TransactionUpdate
) -> Transaction | None:
    row = get_transaction(db, transaction_id)
    if not row:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "amount" in payload and payload["amount"] is not None:
        row.amount = float(payload["amount"])
    if "type" in payload and payload["type"] is not None:
        row.type = TransactionType(payload["type"].value)
    if "category" in payload:
        row.category = payload["category"]
    if "date" in payload:
        row.date = payload["date"]
    if "note" in payload:
        row.note = payload["note"]
    db.commit()
    db.refresh(row)
    return row


def delete_transaction(db: Session, transaction_id: int) -> bool:
    row = get_transaction(db, transaction_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def compute_summary(
    db: Session,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    category: str | None = None,
    transaction_type: TransactionType | None = None,
) -> dict:
    base = select(Transaction)
    base = _apply_filters(
        base,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    rows = list(db.scalars(base).all())

    total_income = Decimal("0")
    total_expense = Decimal("0")
    by_cat: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal("0"), "expense": Decimal("0")}
    )
    by_month: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal("0"), "expense": Decimal("0")}
    )

    for r in rows:
        amt = Decimal(str(r.amount))
        if r.type == TransactionType.income:
            total_income += amt
            by_cat[r.category]["income"] += amt
        else:
            total_expense += amt
            by_cat[r.category]["expense"] += amt
        ym = r.date.strftime("%Y-%m")
        if r.type == TransactionType.income:
            by_month[ym]["income"] += amt
        else:
            by_month[ym]["expense"] += amt

    category_breakdown = []
    for cat, vals in sorted(by_cat.items()):
        inc = vals["income"]
        exp = vals["expense"]
        category_breakdown.append(
            {
                "category": cat,
                "total_income": inc,
                "total_expense": exp,
                "net": inc - exp,
            }
        )

    monthly_summary = []
    for ym in sorted(by_month.keys()):
        inc = by_month[ym]["income"]
        exp = by_month[ym]["expense"]
        monthly_summary.append(
            {
                "year_month": ym,
                "total_income": inc,
                "total_expense": exp,
                "balance": inc - exp,
            }
        )

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "category_breakdown": category_breakdown,
        "monthly_summary": monthly_summary,
    }
