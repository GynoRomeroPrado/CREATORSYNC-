"""
Invoice factoring service.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, date
from sqlalchemy.orm import Session
from decimal import Decimal

from app.db.models import (
    Invoice, Payment, InvoiceStatusEnum,
    PaymentStatusEnum, BrandRiskProfile
)
from app.core.config import settings
from app.services.risk_assessment_service import RiskAssessmentService


class FactoringService:
    """Service for invoice factoring operations."""

    def __init__(self, db: Session):
        self.db = db
        self.risk_service = RiskAssessmentService(db)

    async def submit_invoice(
        self,
        creator_id: int,
        invoice_data: Dict[str, Any]
    ) -> Invoice:
        """
        Submit an invoice for factoring.

        Args:
            creator_id: Creator ID
            invoice_data: Invoice details

        Returns:
            Created Invoice object
        """
        # Validate invoice amount
        amount = invoice_data["invoice_amount"]
        if amount < settings.MIN_INVOICE_AMOUNT:
            raise ValueError(f"Invoice amount must be at least ${settings.MIN_INVOICE_AMOUNT}")
        if amount > settings.MAX_INVOICE_AMOUNT:
            raise ValueError(f"Invoice amount cannot exceed ${settings.MAX_INVOICE_AMOUNT}")

        # Create invoice
        invoice = Invoice(
            creator_id=creator_id,
            invoice_number=invoice_data["invoice_number"],
            invoice_amount=amount,
            currency=invoice_data.get("currency", "USD"),
            brand_name=invoice_data["brand_name"],
            brand_email=invoice_data.get("brand_email"),
            brand_id=invoice_data.get("brand_id"),
            deal_id=invoice_data.get("deal_id"),
            invoice_date=invoice_data["invoice_date"],
            due_date=invoice_data["due_date"],
            invoice_pdf_url=invoice_data["invoice_pdf_url"],
            contract_url=invoice_data.get("contract_url"),
            status=InvoiceStatusEnum.PENDING_REVIEW
        )

        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)

        # Trigger risk assessment
        await self.risk_service.assess_invoice_risk(invoice.id)

        return invoice

    async def approve_invoice(
        self,
        invoice_id: int,
        approved_by: str
    ) -> Dict[str, Any]:
        """
        Approve an invoice for factoring.

        Args:
            invoice_id: Invoice ID
            approved_by: Approver identifier

        Returns:
            Approval details
        """
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status != InvoiceStatusEnum.PENDING_REVIEW:
            raise ValueError(f"Invoice cannot be approved in {invoice.status} status")

        # Check risk score
        if invoice.risk_score < settings.MIN_RISK_SCORE:
            raise ValueError(
                f"Invoice risk score ({invoice.risk_score}) below minimum ({settings.MIN_RISK_SCORE})"
            )

        # Calculate factor fee
        days_until_due = (invoice.due_date - date.today()).days
        periods = max(days_until_due / settings.DEFAULT_DUE_DAYS, 1)
        factor_rate = settings.DEFAULT_FACTOR_RATE * periods

        # Calculate amounts
        advance_amount = invoice.invoice_amount * invoice.advance_rate
        factor_fee = invoice.invoice_amount * factor_rate

        # Update invoice
        invoice.status = InvoiceStatusEnum.APPROVED
        invoice.approved_at = datetime.utcnow()
        invoice.approved_by = approved_by
        invoice.factor_rate = factor_rate
        invoice.factor_fee = factor_fee
        invoice.advance_amount = advance_amount

        self.db.commit()
        self.db.refresh(invoice)

        return {
            "invoice_id": invoice_id,
            "approved": True,
            "advance_rate": invoice.advance_rate,
            "advance_amount": advance_amount,
            "factor_fee": factor_fee,
            "net_advance": advance_amount - factor_fee,
            "expected_return": invoice.invoice_amount - factor_fee
        }

    async def reject_invoice(
        self,
        invoice_id: int,
        reason: str
    ) -> Invoice:
        """Reject an invoice."""
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError("Invoice not found")

        invoice.status = InvoiceStatusEnum.REJECTED
        invoice.rejection_reason = reason

        self.db.commit()
        self.db.refresh(invoice)

        return invoice

    async def fund_invoice(
        self,
        invoice_id: int,
        payment_method: str = "stripe"
    ) -> Payment:
        """
        Fund an approved invoice (send money to creator).

        Args:
            invoice_id: Invoice ID
            payment_method: Payment method (stripe, ach, wire)

        Returns:
            Payment object
        """
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError("Invoice not found")

        if invoice.status != InvoiceStatusEnum.APPROVED:
            raise ValueError("Invoice must be approved before funding")

        # Calculate net advance (advance - fee)
        net_advance = invoice.advance_amount - invoice.factor_fee

        # Create payment record
        payment = Payment(
            invoice_id=invoice_id,
            creator_id=invoice.creator_id,
            amount=net_advance,
            currency=invoice.currency,
            status=PaymentStatusEnum.PENDING,
            payment_method=payment_method
        )

        self.db.add(payment)

        # Update invoice status
        invoice.status = InvoiceStatusEnum.FUNDED
        invoice.funded_at = datetime.utcnow()
        invoice.funded_amount = net_advance

        self.db.commit()
        self.db.refresh(payment)

        # Process payment (would integrate with Stripe/banking here)
        await self._process_payment(payment)

        return payment

    async def _process_payment(self, payment: Payment):
        """Process payment to creator."""
        # This would integrate with Stripe or ACH processing
        # For now, mark as completed
        payment.status = PaymentStatusEnum.COMPLETED
        payment.processed_at = datetime.utcnow()
        payment.transaction_id = f"TXN-{payment.id}-{datetime.utcnow().timestamp()}"

        self.db.commit()

    async def record_payment_received(
        self,
        invoice_id: int,
        amount_received: float,
        payment_date: date
    ) -> Invoice:
        """
        Record that payment was received from brand.

        Args:
            invoice_id: Invoice ID
            amount_received: Amount received
            payment_date: Date payment received

        Returns:
            Updated Invoice
        """
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError("Invoice not found")

        # Calculate late fees if applicable
        late_fees = 0.0
        if payment_date > invoice.due_date:
            days_late = (payment_date - invoice.due_date).days
            months_late = days_late / 30
            late_fees = invoice.invoice_amount * settings.LATE_FEE_RATE * months_late

        # Update invoice
        invoice.status = InvoiceStatusEnum.PAID
        invoice.collected_at = datetime.utcnow()
        invoice.collected_amount = amount_received
        invoice.payment_date = payment_date
        invoice.late_fees = late_fees

        self.db.commit()
        self.db.refresh(invoice)

        # Update brand risk profile
        await self.risk_service._get_brand_risk_profile(invoice.brand_name)

        return invoice

    async def get_factoring_offer(
        self,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get a factoring offer without submitting invoice.

        Args:
            invoice_data: Invoice details

        Returns:
            Offer details
        """
        # Get brand risk profile
        brand_name = invoice_data["brand_name"]
        brand_profile = await self.risk_service._get_brand_risk_profile(brand_name)

        # Create temporary features for assessment
        features = {
            "invoice_amount": invoice_data["invoice_amount"],
            "days_until_due": (invoice_data["due_date"] - date.today()).days,
            "brand_risk_score": brand_profile.risk_score,
            "brand_payment_history": brand_profile.paid_on_time / max(brand_profile.total_invoices, 1),
            "brand_default_rate": brand_profile.defaulted / max(brand_profile.total_invoices, 1),
            "brand_avg_days_to_pay": brand_profile.average_days_to_pay,
            "brand_total_invoices": brand_profile.total_invoices,
            "creator_experience": 1.0,
            "has_contract": 1 if invoice_data.get("contract_url") else 0,
            "has_deal_reference": 1 if invoice_data.get("deal_id") else 0
        }

        # Calculate risk score
        risk_score = self.risk_service._calculate_risk_score(features)
        risk_level = self.risk_service._get_risk_level(risk_score)
        advance_rate = self.risk_service._calculate_advance_rate(risk_score, risk_level)

        # Calculate offer
        invoice_amount = invoice_data["invoice_amount"]
        days_until_due = features["days_until_due"]
        periods = max(days_until_due / settings.DEFAULT_DUE_DAYS, 1)
        factor_rate = settings.DEFAULT_FACTOR_RATE * periods
        advance_amount = invoice_amount * advance_rate
        factor_fee = invoice_amount * factor_rate
        net_advance = advance_amount - factor_fee

        # Calculate ROI for comparison
        roi_annual = (factor_fee / advance_amount) * (365 / days_until_due) * 100

        return {
            "eligible": risk_score >= settings.MIN_RISK_SCORE,
            "risk_score": risk_score,
            "risk_level": risk_level.value,
            "advance_rate": advance_rate,
            "advance_amount": round(advance_amount, 2),
            "factor_fee": round(factor_fee, 2),
            "factor_rate": round(factor_rate * 100, 2),  # As percentage
            "net_advance": round(net_advance, 2),
            "estimated_funding_time": "24-48 hours",
            "roi_annual": round(roi_annual, 2),
            "brand_risk_score": brand_profile.risk_score,
            "brand_payment_history": f"{brand_profile.paid_on_time}/{brand_profile.total_invoices} on time"
        }

    async def get_invoice_stats(self, creator_id: int) -> Dict[str, Any]:
        """Get invoice factoring statistics for a creator."""
        invoices = self.db.query(Invoice).filter(
            Invoice.creator_id == creator_id
        ).all()

        if not invoices:
            return {
                "total_invoices": 0,
                "total_factored": 0,
                "total_received": 0,
                "average_advance_rate": 0,
                "average_funding_time": 0
            }

        funded_invoices = [i for i in invoices if i.status in [
            InvoiceStatusEnum.FUNDED,
            InvoiceStatusEnum.COLLECTING,
            InvoiceStatusEnum.PAID
        ]]

        paid_invoices = [i for i in invoices if i.status == InvoiceStatusEnum.PAID]

        # Calculate funding times
        funding_times = []
        for inv in funded_invoices:
            if inv.funded_at and inv.created_at:
                hours = (inv.funded_at - inv.created_at).total_seconds() / 3600
                funding_times.append(hours)

        return {
            "total_invoices": len(invoices),
            "total_submitted": sum(1 for i in invoices if i.status != InvoiceStatusEnum.PENDING_REVIEW),
            "total_approved": sum(1 for i in invoices if i.status != InvoiceStatusEnum.REJECTED),
            "total_funded": len(funded_invoices),
            "total_factored": sum(i.funded_amount or 0 for i in funded_invoices),
            "total_received": sum(i.collected_amount or 0 for i in paid_invoices),
            "total_fees_paid": sum(i.factor_fee or 0 for i in funded_invoices),
            "average_advance_rate": sum(i.advance_rate or 0 for i in funded_invoices) / len(funded_invoices) if funded_invoices else 0,
            "average_funding_time_hours": sum(funding_times) / len(funding_times) if funding_times else 0,
            "active_invoices": sum(1 for i in invoices if i.status in [InvoiceStatusEnum.FUNDED, InvoiceStatusEnum.COLLECTING])
        }
