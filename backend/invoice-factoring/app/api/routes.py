"""
API routes for Invoice Factoring.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os

from app.db.base import get_db
from app.db.models import Invoice, BrandRiskProfile, Payment, CollectionAttempt
from app.api.schemas import *
from app.services.risk_assessment_service import RiskAssessmentService
from app.services.factoring_service import FactoringService
from app.services.collection_service import CollectionService
from app.core.config import settings

# Routers
invoice_router = APIRouter()
offer_router = APIRouter()
payment_router = APIRouter()
collection_router = APIRouter()
risk_router = APIRouter()
dashboard_router = APIRouter()


# ============================================================================
# INVOICE ROUTES
# ============================================================================

@invoice_router.post("/submit", response_model=InvoiceResponse)
async def submit_invoice(
    creator_id: int,
    invoice: InvoiceSubmit,
    db: Session = Depends(get_db)
):
    """Submit an invoice for factoring."""
    factoring_service = FactoringService(db)

    try:
        result = await factoring_service.submit_invoice(
            creator_id=creator_id,
            invoice_data=invoice.model_dump()
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@invoice_router.get("/creator/{creator_id}", response_model=List[InvoiceResponse])
async def list_invoices(
    creator_id: int,
    status: Optional[InvoiceStatusEnum] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List invoices for a creator."""
    query = db.query(Invoice).filter(Invoice.creator_id == creator_id)

    if status:
        query = query.filter(Invoice.status == status)

    invoices = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()
    return invoices


@invoice_router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get invoice details."""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    return invoice


@invoice_router.post("/{invoice_id}/approve")
async def approve_invoice(
    invoice_id: int,
    approved_by: str = "system",
    db: Session = Depends(get_db)
):
    """Approve an invoice for factoring."""
    factoring_service = FactoringService(db)

    try:
        result = await factoring_service.approve_invoice(invoice_id, approved_by)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@invoice_router.post("/{invoice_id}/reject")
async def reject_invoice(
    invoice_id: int,
    reason: str,
    db: Session = Depends(get_db)
):
    """Reject an invoice."""
    factoring_service = FactoringService(db)

    try:
        result = await factoring_service.reject_invoice(invoice_id, reason)
        return {"invoice_id": invoice_id, "status": "rejected", "reason": reason}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@invoice_router.post("/{invoice_id}/fund", response_model=PaymentResponse)
async def fund_invoice(
    invoice_id: int,
    payment_method: str = "stripe",
    db: Session = Depends(get_db)
):
    """Fund an approved invoice."""
    factoring_service = FactoringService(db)

    try:
        payment = await factoring_service.fund_invoice(invoice_id, payment_method)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@invoice_router.post("/{invoice_id}/record-payment")
async def record_payment(
    invoice_id: int,
    amount_received: float,
    payment_date: date,
    db: Session = Depends(get_db)
):
    """Record that payment was received from brand."""
    factoring_service = FactoringService(db)

    try:
        invoice = await factoring_service.record_payment_received(
            invoice_id, amount_received, payment_date
        )
        return {"invoice_id": invoice_id, "status": "paid", "amount": amount_received}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# FACTORING OFFER ROUTES
# ============================================================================

@offer_router.post("/quote", response_model=FactoringOfferResponse)
async def get_factoring_quote(
    creator_id: int,
    offer_request: FactoringOfferRequest,
    db: Session = Depends(get_db)
):
    """Get a factoring offer/quote without submitting invoice."""
    factoring_service = FactoringService(db)

    offer = await factoring_service.get_factoring_offer(
        invoice_data=offer_request.model_dump()
    )

    return offer


@offer_router.get("/rates")
async def get_current_rates():
    """Get current factoring rates."""
    return {
        "base_factor_rate": settings.DEFAULT_FACTOR_RATE,
        "factor_rate_percentage": settings.DEFAULT_FACTOR_RATE * 100,
        "period_days": settings.DEFAULT_DUE_DAYS,
        "min_advance_rate": settings.MIN_ADVANCE_RATE,
        "max_advance_rate": settings.MAX_ADVANCE_RATE,
        "min_invoice_amount": settings.MIN_INVOICE_AMOUNT,
        "max_invoice_amount": settings.MAX_INVOICE_AMOUNT,
        "example_calculation": {
            "invoice_amount": 10000,
            "advance_rate": 0.90,
            "advance_amount": 9000,
            "factor_fee": 300,  # 3% of 10k
            "net_advance": 8700,
            "you_receive": "Within 24-48 hours"
        }
    }


# ============================================================================
# PAYMENT ROUTES
# ============================================================================

@payment_router.get("/invoice/{invoice_id}", response_model=List[PaymentResponse])
async def get_invoice_payments(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get payments for an invoice."""
    payments = db.query(Payment).filter(
        Payment.invoice_id == invoice_id
    ).all()

    return payments


@payment_router.get("/creator/{creator_id}", response_model=List[PaymentResponse])
async def list_creator_payments(
    creator_id: int,
    status: Optional[PaymentStatusEnum] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List payments for a creator."""
    query = db.query(Payment).filter(Payment.creator_id == creator_id)

    if status:
        query = query.filter(Payment.status == status)

    payments = query.order_by(Payment.initiated_at.desc()).offset(skip).limit(limit).all()
    return payments


# ============================================================================
# COLLECTION ROUTES
# ============================================================================

@collection_router.get("/overdue")
async def get_overdue_invoices(db: Session = Depends(get_db)):
    """Get all overdue invoices."""
    collection_service = CollectionService(db)
    overdue = await collection_service.check_overdue_invoices()

    return {
        "count": len(overdue),
        "invoices": [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "brand_name": inv.brand_name,
                "amount": inv.invoice_amount,
                "due_date": inv.due_date,
                "days_overdue": (date.today() - inv.due_date).days
            }
            for inv in overdue
        ]
    }


@collection_router.post("/{invoice_id}/remind")
async def send_collection_reminder(
    invoice_id: int,
    method: str = "email",
    db: Session = Depends(get_db)
):
    """Send a collection reminder for an invoice."""
    collection_service = CollectionService(db)

    try:
        attempt = await collection_service.send_collection_reminder(invoice_id, method)
        return {
            "invoice_id": invoice_id,
            "reminder_sent": True,
            "attempt_number": attempt.attempt_number,
            "method": method
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@collection_router.get("/{invoice_id}/attempts", response_model=List[CollectionAttemptResponse])
async def get_collection_attempts(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get collection attempts for an invoice."""
    attempts = db.query(CollectionAttempt).filter(
        CollectionAttempt.invoice_id == invoice_id
    ).order_by(CollectionAttempt.attempted_at.desc()).all()

    return attempts


@collection_router.post("/{invoice_id}/escalate")
async def escalate_to_legal(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Escalate invoice to legal collection."""
    collection_service = CollectionService(db)

    try:
        result = await collection_service.escalate_to_legal(invoice_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# RISK ASSESSMENT ROUTES
# ============================================================================

@risk_router.get("/invoice/{invoice_id}", response_model=RiskAssessmentResponse)
async def get_invoice_risk(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Get risk assessment for an invoice."""
    risk_service = RiskAssessmentService(db)

    try:
        assessment = await risk_service.assess_invoice_risk(invoice_id)
        return assessment
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@risk_router.get("/brand/{brand_name}", response_model=BrandRiskProfileResponse)
async def get_brand_risk_profile(
    brand_name: str,
    db: Session = Depends(get_db)
):
    """Get risk profile for a brand."""
    profile = db.query(BrandRiskProfile).filter(
        BrandRiskProfile.brand_name == brand_name
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Brand not found")

    return profile


@risk_router.get("/brands", response_model=List[BrandRiskProfileResponse])
async def list_brand_profiles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all brand risk profiles."""
    profiles = db.query(BrandRiskProfile).order_by(
        BrandRiskProfile.risk_score.desc()
    ).offset(skip).limit(limit).all()

    return profiles


# ============================================================================
# DASHBOARD ROUTE
# ============================================================================

@dashboard_router.get("/creator/{creator_id}", response_model=FactoringDashboard)
async def get_factoring_dashboard(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """Get factoring dashboard for a creator."""
    factoring_service = FactoringService(db)

    # Get stats
    stats = await factoring_service.get_invoice_stats(creator_id)

    # Get recent invoices
    recent_invoices = db.query(Invoice).filter(
        Invoice.creator_id == creator_id
    ).order_by(Invoice.created_at.desc()).limit(5).all()

    # Get upcoming collections
    upcoming = db.query(Invoice).filter(
        Invoice.creator_id == creator_id,
        Invoice.status.in_([InvoiceStatusEnum.FUNDED, InvoiceStatusEnum.COLLECTING]),
        Invoice.due_date >= date.today()
    ).order_by(Invoice.due_date).all()

    upcoming_collections = [
        {
            "invoice_id": inv.id,
            "invoice_number": inv.invoice_number,
            "brand_name": inv.brand_name,
            "amount": inv.invoice_amount,
            "due_date": inv.due_date,
            "days_until_due": (inv.due_date - date.today()).days
        }
        for inv in upcoming
    ]

    # Calculate available funding (simplified)
    available_funding = 250000.0  # Example pool

    return FactoringDashboard(
        creator_id=creator_id,
        total_available_funding=available_funding,
        active_invoices=stats["active_invoices"],
        pending_collection=len(upcoming),
        total_advanced_ytd=stats["total_factored"],
        total_fees_ytd=stats["total_fees_paid"],
        average_funding_time=f"{stats['average_funding_time_hours']:.1f} hours",
        recent_invoices=recent_invoices,
        upcoming_collections=upcoming_collections
    )


@dashboard_router.get("/creator/{creator_id}/stats", response_model=InvoiceStatsResponse)
async def get_invoice_stats(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed invoice statistics."""
    factoring_service = FactoringService(db)
    stats = await factoring_service.get_invoice_stats(creator_id)
    return stats
