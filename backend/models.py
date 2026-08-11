from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())

    transactions = relationship("Transaction", back_populates="user", cascade="all, delete")


class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String)
    is_income = Column(Boolean, default=False)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"))
    amount = Column(Float, nullable=False)
    merchant = Column(String)
    description = Column(String)
    txn_date = Column(Date, nullable=False)
    is_flagged = Column(Boolean, default=False)
    fraud_score = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="transactions")
    category = relationship("Category")


class Budget(Base):
    __tablename__ = "budgets"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    month = Column(String, nullable=False)  # 'YYYY-MM'
    limit_amount = Column(Float, nullable=False)

    category = relationship("Category")


class FraudLog(Base):
    __tablename__ = "fraud_logs"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Float, nullable=False)
    reason = Column(String)
    reviewed = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class ReceiptScan(Base):
    """Audit trail for Phase: OCR Bill Scanner — every upload + what was extracted."""
    __tablename__ = "receipt_scans"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String)
    raw_text = Column(String)
    parsed_amount = Column(Float, nullable=True)
    parsed_merchant = Column(String, nullable=True)
    parsed_date = Column(Date, nullable=True)
    suggested_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    confidence = Column(Float, default=0.0)
    resulting_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class AISuggestion(Base):
    __tablename__ = "ai_suggestions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    kind = Column(String, nullable=False)  # 'budget', 'savings', 'forecast'
    message = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
