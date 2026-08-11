from pydantic import BaseModel, EmailStr
from datetime import date, datetime
from typing import Optional


# ---- Auth ----
class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_admin: bool = False
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---- Transactions ----
class TransactionCreate(BaseModel):
    category_id: int
    amount: float
    merchant: Optional[str] = None
    description: Optional[str] = None
    txn_date: date


class TransactionOut(BaseModel):
    id: int
    category_id: int
    amount: float
    merchant: Optional[str]
    description: Optional[str]
    txn_date: date
    is_flagged: bool
    fraud_score: Optional[float]
    class Config:
        from_attributes = True


# ---- Budgets ----
class BudgetCreate(BaseModel):
    category_id: int
    month: str  # 'YYYY-MM'
    limit_amount: float


class BudgetOut(BaseModel):
    id: int
    category_id: int
    month: str
    limit_amount: float
    class Config:
        from_attributes = True


# ---- Categories ----
class CategoryOut(BaseModel):
    id: int
    name: str
    icon: Optional[str]
    is_income: bool
    class Config:
        from_attributes = True


# ---- Dashboard / ML ----
class ForecastOut(BaseModel):
    month: str
    predicted_spend: float


class FraudCheckOut(BaseModel):
    transaction_id: int
    is_flagged: bool
    fraud_score: float
    reason: str


class AIAdviceOut(BaseModel):
    id: int
    kind: str
    message: str
    class Config:
        from_attributes = True


# ---- OCR Bill Scanner ----
class ReceiptScanOut(BaseModel):
    scan_id: int
    raw_text: str
    parsed_amount: Optional[float] = None
    parsed_merchant: Optional[str] = None
    parsed_date: Optional[date] = None
    suggested_category_id: Optional[int] = None
    suggested_category_name: Optional[str] = None
    confidence: float


# ---- Admin ----
class AdminUserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_admin: bool
    is_active: bool
    created_at: datetime
    transaction_count: int = 0
    total_spent: float = 0.0
    flagged_count: int = 0
    class Config:
        from_attributes = True


class AdminStatsOut(BaseModel):
    total_users: int
    active_users: int
    total_transactions: int
    total_flagged: int
    total_volume: float
    total_receipt_scans: int
    signups_last_7_days: int


class AdminFraudLogOut(BaseModel):
    id: int
    transaction_id: int
    user_id: int
    user_email: EmailStr
    score: float
    reason: Optional[str]
    reviewed: bool
    created_at: datetime
    class Config:
        from_attributes = True
