"""
Pydantic schemas for Invoice Factoring API.
"""
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr

from app.db.models import (
    InvoiceStatusEnum, PaymentStatusEnum,
    RiskLevelEnum
)


# Invoice Schemas
class InvoiceSubmit(BaseModel):
    invoice_number: str
    invoice_amount: float = Field(gt=0)
    currency: str = "USD"
    brand_name: str
    brand_email: Optional[EmailStr] = None
    brand_id: Optional[int] = None
    deal_id: Optional[int] = None
    invoice_date: date
    due_date: date
    invoice_pdf_url: str
    contract_url: Optional[str] = None


class InvoiceResponse(BaseModel):
    id: int
    creator_id: int
    invoice_number: str
    invoice_amount: float
    currency: str
    brand_name: str
    invoice_date: date
    due_date: date
    status: InvoiceStatusEnum
    risk_score: Optional[int]
    risk_level: Optional[RiskLevelEnum]
    advance_rate: Optional[float]
    advance_amount: Optional[float]
    factor_fee: Optional[float]
    funded_amount: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


# Factoring Offer
class FactoringOfferRequest(BaseModel):
    invoice_amount: float = Field(gt=0)
    brand_name: str
    due_date: date
    contract_url: Optional[str] = None
    deal_id: Optional[int] = None


class FactoringOfferResponse(BaseModel):
    eligible: bool
    risk_score: int
    risk_level: str
    advance_rate: float
    advance_amount: float
    factor_fee: float
    factor_rate: float
    net_advance: float
    estimated_funding_time: str
    roi_annual: float
    brand_risk_score: int
    brand_payment_history: str


# Risk Assessment
class RiskAssessmentResponse(BaseModel):
    invoice_id: int
    risk_score: int
    risk_level: str
    risk_factors: Dict[str, Any]
    advance_rate: float
    recommended: bool
    max_advance_amount: float


# Payment
class PaymentResponse(BaseModel):
    id: int
    invoice_id: int
    amount: float
    currency: str
    status: PaymentStatusEnum
    payment_method: str
    transaction_id: Optional[str]
    initiated_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


# Brand Risk Profile
class BrandRiskProfileResponse(BaseModel):
    id: int
    brand_name: str
    risk_score: int
    risk_level: RiskLevelEnum
    total_invoices: int
    paid_on_time: int
    paid_late: int
    defaulted: int
    average_days_to_pay: float
    last_assessed: datetime

    class Config:
        from_attributes = True


# Collection
class CollectionAttemptResponse(BaseModel):
    id: int
    invoice_id: int
    attempt_number: int
    method: str
    sent_to: str
    attempted_at: datetime
    response_received: bool

    class Config:
        from_attributes = True


# Statistics
class InvoiceStatsResponse(BaseModel):
    total_invoices: int
    total_submitted: int
    total_approved: int
    total_funded: int
    total_factored: float
    total_received: float
    total_fees_paid: float
    average_advance_rate: float
    average_funding_time_hours: float
    active_invoices: int


# Dashboard
class FactoringDashboard(BaseModel):
    creator_id: int
    total_available_funding: float
    active_invoices: int
    pending_collection: int
    total_advanced_ytd: float
    total_fees_ytd: float
    average_funding_time: str
    recent_invoices: List[InvoiceResponse]
    upcoming_collections: List[Dict[str, Any]]
