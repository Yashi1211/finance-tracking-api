from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.security import decode_token

_role_header = APIKeyHeader(name="X-Role", auto_error=False)
_bearer = HTTPBearer(auto_error=False)


def get_role(
    db: Session = Depends(get_db),
    bearer: HTTPAuthorizationCredentials | None = Depends(_bearer),
    x_role: str | None = Depends(_role_header),
) -> UserRole:
    if bearer and bearer.credentials:
        payload = decode_token(bearer.credentials)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        user_id = payload.get("sub")
        try:
            uid = int(user_id)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token subject",
            )
        user = db.get(User, uid)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User no longer exists",
            )
        return UserRole(user.role.value)

    if x_role and x_role.strip():
        key = x_role.strip().lower()
        try:
            return UserRole(key)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role '{x_role}'. Allowed: viewer, analyst, admin",
            )

    return UserRole.admin


def require_viewer(role: UserRole = Depends(get_role)) -> UserRole:
    return role


def require_analyst(role: UserRole = Depends(get_role)) -> UserRole:
    if role == UserRole.viewer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst or admin role required for this action",
        )
    return role


def require_admin(role: UserRole = Depends(get_role)) -> UserRole:
    if role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required for this action",
        )
    return role
