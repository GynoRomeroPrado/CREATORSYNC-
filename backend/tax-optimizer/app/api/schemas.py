"""
Pydantic schemas for Tax Optimizer API.
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from app.db.models import ExpenseCategoryEnum, ExpenseProcessingStatusEnum, TaxFormTypeEnum


# Expense Schemas
class ExpenseBase(BaseModel):
    amount: float = Field(gt=0)
    currency: str = "USD"
    category: ExpenseCategoryEnum
    description: str
    vendor: Optional[str] = None
    expense_date: date


class ExpenseCreate(ExpenseBase):
    receipt_filename: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    id: int
    creator_id: int
    receipt_url: Optional[str]
    ocr_confidence: Optional[float]
    auto_categorized: bool
    category_confidence: Optional[float]
    deductible: bool
    deduction_percentage: float
    processing_status: ExpenseProcessingStatusEnum
    created_at: datetime

    class Config:
        from_attributes = True


# Receipt Upload Schema
class ReceiptUploadResponse(BaseModel):
    expense_id: int
    filename: str
    ocr_text: Optional[str]
    extracted_data: Dict[str, Any]
    suggested_category: str
    category_confidence: float


# Bank Account Schemas
class BankAccountConnect(BaseModel):
    plaid_public_token: str


class BankAccountResponse(BaseModel):
    id: int
    account_name: Optional[str]
    account_type: Optional[str]
    account_mask: Optional[str]
    institution_name: Optional[str]
    is_active: bool
    last_synced_at: Optional[datetime]

    class Config:
        from_attributes = True


# Tax Deduction Schemas
class TaxDeductionResponse(BaseModel):
    id: int
    category: ExpenseCategoryEnum
    total_amount: float
    deductible_amount: float
    expense_count: int

    class Config:
        from_attributes = True


class DeductionSummary(BaseModel):
    tax_year: int
    total_deductions: float
    by_category: Dict[str, Dict[str, Any]]
    standard_deduction: float
    recommendation: str  # "itemize" or "standard"


# Quarterly Tax Estimate Schemas
class QuarterlyEstimateResponse(BaseModel):
    id: int
    tax_year: int
    quarter: int
    gross_income: float
    net_income: float
    federal_income_tax: float
    self_employment_tax: float
    state_tax: float
    total_tax_owed: float
    due_date: date
    paid: bool

    class Config:
        from_attributes = True


# Tax Form Schemas
class TaxForm1099Request(BaseModel):
    payer_info: Dict[str, str] = Field(
        example={
            "name": "Brand Inc.",
            "address": "123 Main St",
            "city_state_zip": "New York, NY 10001",
            "tin": "12-3456789"
        }
    )
    recipient_info: Dict[str, str]
    nonemployee_compensation: float


class TaxFormScheduleCRequest(BaseModel):
    business_info: Dict[str, str] = Field(
        example={"description": "Content Creator"}
    )
    income_data: Dict[str, float]
    expense_data: Dict[str, float]


class TaxFormW9Request(BaseModel):
    taxpayer_info: Dict[str, str] = Field(
        example={
            "name": "John Doe",
            "business_name": "John Doe Media",
            "classification": "Individual/sole proprietor",
            "address": "456 Creator Ave",
            "city_state_zip": "Los Angeles, CA 90001",
            "tin": "123-45-6789"
        }
    )


class TaxFormResponse(BaseModel):
    id: int
    form_type: TaxFormTypeEnum
    tax_year: int
    pdf_url: str
    pdf_filename: str
    is_finalized: bool
    generated_at: datetime

    class Config:
        from_attributes = True


# Home Office Deduction Schema
class HomeOfficeRequest(BaseModel):
    method: str = Field(pattern="^(simplified|actual)$")
    square_feet: Optional[float] = None
    home_area_total: Optional[float] = None
    office_area: Optional[float] = None
    expenses: Optional[Dict[str, float]] = None


class HomeOfficeResponse(BaseModel):
    id: int
    tax_year: int
    method: str
    square_feet: Optional[float]
    business_percentage: Optional[float]
    total_deduction: float
    calculated_at: datetime

    class Config:
        from_attributes = True


# Dashboard Schema
class TaxDashboard(BaseModel):
    creator_id: int
    tax_year: int
    ytd_income: float
    ytd_expenses: float
    ytd_deductions: float
    estimated_tax_owed: float
    next_payment_due: Optional[date]
    next_payment_amount: Optional[float]
    expense_summary: Dict[str, float]
    top_deductions: List[TaxDeductionResponse]
