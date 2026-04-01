from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.security import hash_password


def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username.strip().lower())
    return db.scalars(stmt).first()


def create_user(
    db: Session, *, username: str, password: str, role: UserRole
) -> User:
    u = User(
        username=username.strip().lower(),
        hashed_password=hash_password(password),
        role=role,
    )
    db.add(u)
    db.commit()
    db.refresh(u)
    return u
