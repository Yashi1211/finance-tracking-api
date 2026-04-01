from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.deps import UserRole, require_admin, require_analyst, require_viewer
from app.models import TransactionType
from app.schemas import (
    TransactionCreate,
    TransactionListResponse,
    TransactionRead,
    TransactionUpdate,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _has_filters(
    date_from: date | None,
    date_to: date | None,
    category: str | None,
    transaction_type: TransactionType | None,
) -> bool:
    return any(
        x is not None
        for x in (date_from, date_to, category, transaction_type)
    )


@router.post(
    "",
    response_model=TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    body: TransactionCreate,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_admin),
):
    return crud.create_transaction(db, body)


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    db: Session = Depends(get_db),
    role: UserRole = Depends(require_viewer),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    category: str | None = Query(None, min_length=1, max_length=100),
    transaction_type: TransactionType | None = Query(None, alias="type"),
):
    if _has_filters(date_from, date_to, category, transaction_type):
        if role == UserRole.viewer:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Viewers cannot filter. Use analyst or admin role.",
            )
    total = crud.count_transactions(
        db,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
    )
    items = crud.list_transactions(
        db,
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
        skip=skip,
        limit=limit,
    )
    return TransactionListResponse(
        items=items, total=total, skip=skip, limit=limit
    )


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_viewer),
):
    row = crud.get_transaction(db, transaction_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return row


@router.patch("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: int,
    body: TransactionUpdate,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_admin),
):
    if body.model_dump(exclude_unset=True) == {}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    row = crud.update_transaction(db, transaction_id, body)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return row


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    _: UserRole = Depends(require_admin),
):
    if not crud.delete_transaction(db, transaction_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
