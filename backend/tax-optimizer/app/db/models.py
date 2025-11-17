"""
Database models for Tax Optimizer.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean,
    ForeignKey, JSON, Text, Enum as SQLEnum, Index, Date
)
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class ExpenseCategoryEnum(str, enum.Enum):
    """Expense categories for creators."""
    EQUIPMENT = "equipment"  # Cameras, computers, etc.
    SOFTWARE = "software"  # Subscriptions, tools
    TRAVEL = "travel"  # Business travel
    MEALS = "meals"  # Business meals
    HOME_OFFICE = "home_office"  # Home office expenses
    UTILITIES = "utilities"  # Internet, phone
    ADVERTISING = "advertising"  # Paid promotions
    PROFESSIONAL_SERVICES = "professional_services"  # Accountant, lawyer
    EDUCATION = "education"  # Courses, training
    SUPPLIES = "supplies"  # General supplies
    INSURANCE = "insurance"  # Business insurance
    OTHER = "other"


class ExpenseProcessingStatusEnum(str, enum.Enum):
    """Status of expense processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class TaxFormTypeEnum(str, enum.Enum):
    """Tax form types."""
    FORM_1099_NEC = "1099-nec"  # Nonemployee compensation
    FORM_1099_MISC = "1099-misc"  # Miscellaneous income
    SCHEDULE_C = "schedule-c"  # Profit or loss from business
    SCHEDULE_SE = "schedule-se"  # Self-employment tax
    FORM_W9 = "w9"  # Request for taxpayer ID


class Expense(Base):
    """Expense records."""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)  # FK to creators table

    # Expense details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    category = Column(SQLEnum(ExpenseCategoryEnum), nullable=False)

    # Description
    description = Column(Text, nullable=False)
    vendor = Column(String, nullable=True)

    # Date
    expense_date = Column(Date, nullable=False)

    # Receipt
    receipt_url = Column(String, nullable=True)  # S3/local path
    receipt_filename = Column(String, nullable=True)

    # OCR data
    ocr_text = Column(Text, nullable=True)
    ocr_confidence = Column(Float, nullable=True)
    ocr_data = Column(JSON, nullable=True)  # Structured data from OCR

    # Categorization
    auto_categorized = Column(Boolean, default=False)
    category_confidence = Column(Float, nullable=True)
    manual_category_override = Column(Boolean, default=False)

    # Tax details
    deductible = Column(Boolean, default=True)
    deduction_percentage = Column(Float, default=100.0)  # Partial deductions
    tax_year = Column(Integer, nullable=False)

    # Processing
    processing_status = Column(SQLEnum(ExpenseProcessingStatusEnum), default=ExpenseProcessingStatusEnum.PENDING)

    # Banking integration
    plaid_transaction_id = Column(String, nullable=True)
    bank_account_id = Column(String, nullable=True)

    # Metadata
    notes = Column(Text, nullable=True)
    metadata = Column(JSON, default={})

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_expense_creator_date', 'creator_id', 'expense_date'),
        Index('ix_expense_category', 'category'),
    )


class BankAccount(Base):
    """Connected bank accounts via Plaid."""
    __tablename__ = "bank_accounts"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)

    # Plaid details
    plaid_access_token = Column(Text, nullable=False)  # Encrypted in production
    plaid_item_id = Column(String, nullable=False)
    plaid_account_id = Column(String, nullable=False)

    # Account info
    account_name = Column(String, nullable=True)
    account_type = Column(String, nullable=True)  # checking, savings, credit
    account_mask = Column(String, nullable=True)  # Last 4 digits
    institution_name = Column(String, nullable=True)

    # Status
    is_active = Column(Boolean, default=True)
    last_synced_at = Column(DateTime, nullable=True)

    # Timestamps
    connected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaxDeduction(Base):
    """Tax deduction calculations."""
    __tablename__ = "tax_deductions"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)
    tax_year = Column(Integer, nullable=False)

    # Deduction details
    category = Column(SQLEnum(ExpenseCategoryEnum), nullable=False)
    total_amount = Column(Float, nullable=False)
    deductible_amount = Column(Float, nullable=False)

    # Calculation details
    expense_count = Column(Integer, default=0)
    calculation_method = Column(String, nullable=True)
    calculation_details = Column(JSON, default={})

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_deduction_creator_year', 'creator_id', 'tax_year'),
    )


class QuarterlyTaxEstimate(Base):
    """Quarterly tax estimates."""
    __tablename__ = "quarterly_tax_estimates"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)

    # Period
    tax_year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)  # 1-4

    # Income
    gross_income = Column(Float, nullable=False)
    net_income = Column(Float, nullable=False)  # After expenses

    # Tax calculations
    federal_income_tax = Column(Float, nullable=False)
    self_employment_tax = Column(Float, nullable=False)
    state_tax = Column(Float, default=0.0)
    total_tax_owed = Column(Float, nullable=False)

    # Deductions
    total_deductions = Column(Float, nullable=False)
    standard_deduction = Column(Float, default=0.0)

    # Payment
    due_date = Column(Date, nullable=False)
    paid = Column(Boolean, default=False)
    paid_date = Column(Date, nullable=True)
    paid_amount = Column(Float, nullable=True)

    # Metadata
    calculation_details = Column(JSON, default={})

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_quarterly_creator_year_quarter', 'creator_id', 'tax_year', 'quarter'),
    )


class TaxForm(Base):
    """Generated tax forms."""
    __tablename__ = "tax_forms"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)

    # Form details
    form_type = Column(SQLEnum(TaxFormTypeEnum), nullable=False)
    tax_year = Column(Integer, nullable=False)

    # Data
    form_data = Column(JSON, nullable=False)  # All form fields

    # Files
    pdf_url = Column(String, nullable=True)  # Generated PDF path
    pdf_filename = Column(String, nullable=True)

    # Status
    is_finalized = Column(Boolean, default=False)
    finalized_at = Column(DateTime, nullable=True)

    # E-filing
    efiled = Column(Boolean, default=False)
    efile_confirmation = Column(String, nullable=True)

    # Timestamps
    generated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_form_creator_year', 'creator_id', 'tax_year'),
    )


class HomeOfficeDeduction(Base):
    """Home office deduction calculations."""
    __tablename__ = "home_office_deductions"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, nullable=False)
    tax_year = Column(Integer, nullable=False)

    # Method: simplified or actual
    method = Column(String, nullable=False)

    # Simplified method (up to 300 sq ft @ $5/sq ft)
    square_feet = Column(Float, nullable=True)

    # Actual method
    home_area_total = Column(Float, nullable=True)  # Total sq ft
    office_area = Column(Float, nullable=True)  # Office sq ft
    business_percentage = Column(Float, nullable=True)  # office/total

    # Expenses (for actual method)
    mortgage_interest = Column(Float, default=0.0)
    property_tax = Column(Float, default=0.0)
    utilities = Column(Float, default=0.0)
    insurance = Column(Float, default=0.0)
    repairs = Column(Float, default=0.0)
    depreciation = Column(Float, default=0.0)

    # Calculated deduction
    total_deduction = Column(Float, nullable=False)

    # Metadata
    calculation_details = Column(JSON, default={})

    # Timestamps
    calculated_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('ix_home_office_creator_year', 'creator_id', 'tax_year'),
    )
