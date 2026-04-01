from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import UserRole, require_analyst, require_viewer
from app.models import TransactionType
from app.schemas import SummaryFull, SummaryViewer

router = APIRouter(prefix="/summary", tags=["summary"])


@router.get("/viewer", response_model=SummaryViewer)
def summary_viewer(
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_viewer),
):
    """Totals only — all roles may call; intended for viewer workflow."""
    data = crud.compute_summary(db)
    return SummaryViewer(
        total_income=data["total_income"],
        total_expense=data["total_expense"],
        balance=data["balance"],
    )


@router.get("", response_model=SummaryFull)
def summary_full(
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_analyst),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category: str | None = Query(None, min_length=1, max_length=100),
    transaction_type: TransactionType | None = Query(None, alias="type"),
):
    """
    Full insights: category breakdown + monthly summary.
    Same filter query params as GET /transactions (analyst & admin).
    """
    data = crud.compute_summary(
        db,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    return SummaryFull(**data)
