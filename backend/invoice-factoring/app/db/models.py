"""
Database models for Invoice Factoring.
"""
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, JSON, Text, Enum as SQLEnum, Index, Date
)
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class InvoiceStatusEnum(str, enum.Enum):
    """Invoice status."""
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    FUNDED = "funded"
    COLLECTING = "collecting"
    PAID = "paid"
    DEFAULTED = "defaulted"


class PaymentStatusEnum(str, enum.Enum):
    """Payment status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class RiskLevelEnum(str, enum.Enum):
    """Risk level assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class Invoice(Base):
    """Invoice submitted for factoring."""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)

    # Invoice details
    invoice_number = Column(String, unique=True, nullable=False)
    invoice_amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")

    # Brand/Client info
    brand_name = Column(String, nullable=False)
    brand_email = Column(String, nullable=True)
    brand_id = Column(Integer, nullable=True)  # FK to brands table if exists

    # Deal reference
    deal_id = Column(Integer, nullable=True)  # FK to deals table from CRM

    # Dates
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    payment_date = Column(Date, nullable=True)

    # Documents
    invoice_pdf_url = Column(String, nullable=False)
    contract_url = Column(String, nullable=True)

    # Factoring details
    status = Column(SQLEnum(InvoiceStatusEnum), default=InvoiceStatusEnum.PENDING_REVIEW)
    advance_rate = Column(Float, nullable=True)  # 0.80 - 0.95
    advance_amount = Column(Float, nullable=True)  # Amount to advance
    factor_fee = Column(Float, nullable=True)  # Fee amount
    factor_rate = Column(Float, nullable=True)  # Fee rate (e.g., 0.03)

    # Risk assessment
    risk_score = Column(Integer, nullable=True)  # 0-100
    risk_level = Column(SQLEnum(RiskLevelEnum), nullable=True)
    risk_factors = Column(JSON, nullable=True)

    # Approval
    approved_at = Column(DateTime, nullable=True)
    approved_by = Column(String, nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Funding
    funded_at = Column(DateTime, nullable=True)
    funded_amount = Column(Float, nullable=True)
    payment_transaction_id = Column(String, nullable=True)

    # Collection
    collected_at = Column(DateTime, nullable=True)
    collected_amount = Column(Float, nullable=True)
    late_fees = Column(Float, default=0.0)

    # Status tracking
    is_verified = Column(Boolean, default=False)
    kyc_completed = Column(Boolean, default=False)

    # Metadata
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = relationship("Payment", back_populates="invoice")
    collection_attempts = relationship("CollectionAttempt", back_populates="invoice")

    __table_args__ = (
        Index('ix_invoice_creator', 'creator_id'),
        Index('ix_invoice_status', 'status'),
    )


class BrandRiskProfile(Base):
    """Risk profile for brands/clients."""
    __tablename__ = "brand_risk_profiles"

    id = Column(Integer, primary_key=True, index=True)
    brand_name = Column(String, nullable=False, unique=True)
    brand_id = Column(Integer, nullable=True)  # FK to brands table

    # Risk scoring
    risk_score = Column(Integer, nullable=False)  # 0-100
    risk_level = Column(SQLEnum(RiskLevelEnum), nullable=False)

    # Payment history
    total_invoices = Column(Integer, default=0)
    paid_on_time = Column(Integer, default=0)
    paid_late = Column(Integer, default=0)
    defaulted = Column(Integer, default=0)

    # Financial metrics
    average_invoice_amount = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)
    average_days_to_pay = Column(Float, default=0.0)

    # Company info
    company_size = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    years_in_business = Column(Integer, nullable=True)
    credit_rating = Column(String, nullable=True)

    # Risk factors
    risk_factors = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_assessed = Column(DateTime, default=datetime.utcnow)


class Payment(Base):
    """Payments made to creators for invoice factoring."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    creator_id = Column(Integer, nullable=False)

    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(SQLEnum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)

    # Processing
    payment_method = Column(String, nullable=False)  # stripe, ach, wire
    transaction_id = Column(String, nullable=True)
    stripe_payment_id = Column(String, nullable=True)

    # Bank details (encrypted in production)
    bank_account_number = Column(String, nullable=True)
    bank_routing_number = Column(String, nullable=True)

    # Timing
    initiated_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)

    # Metadata
    metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="payments")


class CollectionAttempt(Base):
    """Collection attempts for invoices."""
    __tablename__ = "collection_attempts"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)

    # Attempt details
    attempt_number = Column(Integer, nullable=False)
    method = Column(String, nullable=False)  # email, phone, letter, legal

    # Communication
    sent_to = Column(String, nullable=False)
    message_content = Column(Text, nullable=True)
    response_received = Column(Boolean, default=False)
    response_content = Column(Text, nullable=True)

    # Status
    successful = Column(Boolean, default=False)
    payment_promised_date = Column(Date, nullable=True)

    # Timestamps
    attempted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice", back_populates="collection_attempts")


class InvestorPool(Base):
    """Pool of investors funding the factoring."""
    __tablename__ = "investor_pools"

    id = Column(Integer, primary_key=True, index=True)

    # Investor info
    investor_name = Column(String, nullable=False)
    investor_email = Column(String, nullable=False)

    # Capital
    total_capital = Column(Float, nullable=False)
    available_capital = Column(Float, nullable=False)
    deployed_capital = Column(Float, default=0.0)

    # Performance
    total_invested = Column(Float, default=0.0)
    total_returned = Column(Float, default=0.0)
    total_profit = Column(Float, default=0.0)
    roi_percentage = Column(Float, default=0.0)

    # Risk preference
    max_risk_level = Column(SQLEnum(RiskLevelEnum), default=RiskLevelEnum.MEDIUM)
    min_investment = Column(Float, default=1000.0)
    max_investment = Column(Float, default=50000.0)

    # Status
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class KYCVerification(Base):
    """KYC/AML verification records."""
    __tablename__ = "kyc_verifications"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)

    # Verification details
    verification_status = Column(String, nullable=False)  # pending, approved, rejected
    verification_provider = Column(String, nullable=True)  # jumio, onfido, etc.
    verification_id = Column(String, nullable=True)

    # Identity documents
    id_document_type = Column(String, nullable=True)
    id_document_number = Column(String, nullable=True)
    id_verification_url = Column(String, nullable=True)

    # Address verification
    address_verified = Column(Boolean, default=False)
    proof_of_address_url = Column(String, nullable=True)

    # Bank verification
    bank_verified = Column(Boolean, default=False)
    plaid_access_token = Column(Text, nullable=True)

    # Results
    approved = Column(Boolean, default=False)
    rejection_reason = Column(Text, nullable=True)

    # Timestamps
    submitted_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
