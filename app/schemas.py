import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionTypeSchema(str, Enum):
    income = "income"
    expense = "expense"


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Must be positive")
    type: TransactionTypeSchema
    category: str = Field(..., min_length=1, max_length=100)
    date: datetime.date
    note: str | None = Field(None, max_length=2000)

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("category cannot be empty")
        return v.strip()


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    amount: Decimal | None = Field(None, gt=0)
    type: TransactionTypeSchema | None = None
    category: str | None = Field(None, min_length=1, max_length=100)
    date: datetime.date | None = None
    note: str | None = Field(None, max_length=2000)

    @field_validator("category")
    @classmethod
    def category_not_blank(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not v.strip():
            raise ValueError("category cannot be empty")
        return v.strip()


class TransactionRead(TransactionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class TransactionListResponse(BaseModel):
    items: list[TransactionRead]
    total: int
    skip: int
    limit: int


class CategoryBreakdownItem(BaseModel):
    category: str
    total_income: Decimal
    total_expense: Decimal
    net: Decimal


class MonthlySummaryItem(BaseModel):
    year_month: str
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


class SummaryFull(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    category_breakdown: list[CategoryBreakdownItem]
    monthly_summary: list[MonthlySummaryItem]


class SummaryViewer(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal


class UserRoleSchema(str, Enum):
    viewer = "viewer"
    analyst = "analyst"
    admin = "admin"


class UserRegister(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    password: str = Field(..., min_length=4, max_length=128)
    role: UserRoleSchema = UserRoleSchema.viewer


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: UserRoleSchema


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
