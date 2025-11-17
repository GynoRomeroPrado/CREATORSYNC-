"""
Risk assessment service using ML.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

from app.db.models import (
    Invoice, BrandRiskProfile, RiskLevelEnum,
    InvoiceStatusEnum
)
from app.core.config import settings


class RiskAssessmentService:
    """Service for assessing invoice factoring risk."""

    def __init__(self, db: Session):
        self.db = db
        self.model_path = os.path.join(
            settings.MODEL_PATH,
            "risk_model.pkl"
        )
        self.model = self._load_or_create_model()

    def _load_or_create_model(self) -> RandomForestClassifier:
        """Load existing model or create new one."""
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)

        # Create new model
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        return model

    async def assess_invoice_risk(
        self,
        invoice_id: int
    ) -> Dict[str, Any]:
        """
        Assess risk for an invoice.

        Args:
            invoice_id: Invoice ID

        Returns:
            Dictionary with risk assessment
        """
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError("Invoice not found")

        # Get or create brand risk profile
        brand_profile = await self._get_brand_risk_profile(invoice.brand_name)

        # Extract features
        features = self._extract_risk_features(invoice, brand_profile)

        # Calculate risk score
        risk_score = self._calculate_risk_score(features)

        # Determine risk level
        risk_level = self._get_risk_level(risk_score)

        # Identify risk factors
        risk_factors = self._identify_risk_factors(features, invoice, brand_profile)

        # Calculate recommended advance rate
        advance_rate = self._calculate_advance_rate(risk_score, risk_level)

        # Update invoice
        invoice.risk_score = risk_score
        invoice.risk_level = risk_level
        invoice.risk_factors = risk_factors
        invoice.advance_rate = advance_rate
        self.db.commit()

        return {
            "invoice_id": invoice_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "advance_rate": advance_rate,
            "recommended": risk_score >= settings.MIN_RISK_SCORE,
            "max_advance_amount": invoice.invoice_amount * advance_rate
        }

    async def _get_brand_risk_profile(
        self,
        brand_name: str
    ) -> BrandRiskProfile:
        """Get or create brand risk profile."""
        profile = self.db.query(BrandRiskProfile).filter(
            BrandRiskProfile.brand_name == brand_name
        ).first()

        if profile:
            # Update profile with latest data
            await self._update_brand_profile(profile)
            return profile

        # Create new profile
        profile = BrandRiskProfile(
            brand_name=brand_name,
            risk_score=50,  # Default neutral score
            risk_level=RiskLevelEnum.MEDIUM
        )
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)

        return profile

    async def _update_brand_profile(self, profile: BrandRiskProfile):
        """Update brand risk profile with latest payment history."""
        # Get all invoices for this brand
        invoices = self.db.query(Invoice).filter(
            Invoice.brand_name == profile.brand_name
        ).all()

        if not invoices:
            return

        # Calculate metrics
        total_invoices = len(invoices)
        paid_invoices = [i for i in invoices if i.status == InvoiceStatusEnum.PAID]
        late_invoices = [i for i in invoices if i.late_fees > 0]
        defaulted_invoices = [i for i in invoices if i.status == InvoiceStatusEnum.DEFAULTED]

        # Average payment time
        days_to_pay = []
        for inv in paid_invoices:
            if inv.payment_date and inv.due_date:
                days = (inv.payment_date - inv.due_date).days
                days_to_pay.append(days)

        # Update profile
        profile.total_invoices = total_invoices
        profile.paid_on_time = len([i for i in paid_invoices if i not in late_invoices])
        profile.paid_late = len(late_invoices)
        profile.defaulted = len(defaulted_invoices)
        profile.average_invoice_amount = sum(i.invoice_amount for i in invoices) / total_invoices
        profile.total_paid = sum(i.collected_amount or 0 for i in paid_invoices)
        profile.average_days_to_pay = sum(days_to_pay) / len(days_to_pay) if days_to_pay else 0
        profile.last_assessed = datetime.utcnow()

        # Recalculate risk score
        profile.risk_score = self._calculate_brand_risk_score(profile)
        profile.risk_level = self._get_risk_level(profile.risk_score)

        self.db.commit()

    def _calculate_brand_risk_score(self, profile: BrandRiskProfile) -> int:
        """Calculate risk score for a brand."""
        score = 100  # Start with perfect score

        # Payment history (40% weight)
        if profile.total_invoices > 0:
            on_time_rate = profile.paid_on_time / profile.total_invoices
            score -= (1 - on_time_rate) * 40

        # Default rate (30% weight)
        if profile.total_invoices > 0:
            default_rate = profile.defaulted / profile.total_invoices
            score -= default_rate * 30

        # Average days to pay (20% weight)
        if profile.average_days_to_pay > 0:
            late_penalty = min(profile.average_days_to_pay / 30, 1.0) * 20
            score -= late_penalty

        # Invoice volume (10% weight) - more invoices = more reliable
        if profile.total_invoices < 5:
            score -= 10 * (1 - profile.total_invoices / 5)

        return max(0, int(score))

    def _extract_risk_features(
        self,
        invoice: Invoice,
        brand_profile: BrandRiskProfile
    ) -> Dict[str, Any]:
        """Extract features for risk assessment."""
        # Invoice features
        invoice_amount = invoice.invoice_amount
        days_until_due = (invoice.due_date - datetime.now().date()).days

        # Brand features
        brand_risk_score = brand_profile.risk_score
        brand_payment_history = brand_profile.paid_on_time / max(brand_profile.total_invoices, 1)
        brand_default_rate = brand_profile.defaulted / max(brand_profile.total_invoices, 1)
        brand_avg_days = brand_profile.average_days_to_pay

        # Creator features (would fetch from attribution engine)
        creator_experience = 1.0  # Placeholder

        return {
            "invoice_amount": invoice_amount,
            "days_until_due": days_until_due,
            "brand_risk_score": brand_risk_score,
            "brand_payment_history": brand_payment_history,
            "brand_default_rate": brand_default_rate,
            "brand_avg_days_to_pay": brand_avg_days,
            "brand_total_invoices": brand_profile.total_invoices,
            "creator_experience": creator_experience,
            "has_contract": 1 if invoice.contract_url else 0,
            "has_deal_reference": 1 if invoice.deal_id else 0
        }

    def _calculate_risk_score(self, features: Dict[str, Any]) -> int:
        """Calculate overall risk score."""
        # Weighted scoring
        score = 100

        # Brand risk (50% weight)
        score = score * 0.5 + features["brand_risk_score"] * 0.5

        # Payment history (20% weight)
        payment_history_score = features["brand_payment_history"] * 100
        score = score * 0.8 + payment_history_score * 0.2

        # Default rate penalty (20% weight)
        default_penalty = features["brand_default_rate"] * 100
        score -= default_penalty * 0.2

        # Documentation bonus (10% weight)
        if features["has_contract"] and features["has_deal_reference"]:
            score += 10

        # Invoice amount risk
        if features["invoice_amount"] > 50000:
            score -= 5  # Higher amounts are riskier

        # Time until due
        if features["days_until_due"] < 7:
            score -= 10  # Very short payment window

        return max(0, min(100, int(score)))

    def _get_risk_level(self, risk_score: int) -> RiskLevelEnum:
        """Determine risk level from score."""
        if risk_score >= settings.LOW_RISK_THRESHOLD:
            return RiskLevelEnum.LOW
        elif risk_score >= settings.HIGH_RISK_THRESHOLD:
            return RiskLevelEnum.MEDIUM
        elif risk_score >= settings.MIN_RISK_SCORE:
            return RiskLevelEnum.HIGH
        else:
            return RiskLevelEnum.VERY_HIGH

    def _identify_risk_factors(
        self,
        features: Dict[str, Any],
        invoice: Invoice,
        brand_profile: BrandRiskProfile
    ) -> Dict[str, Any]:
        """Identify specific risk factors."""
        factors = {}

        # Brand history
        if brand_profile.total_invoices < 3:
            factors["limited_history"] = "Brand has limited payment history"

        if brand_profile.defaulted > 0:
            factors["past_defaults"] = f"Brand has {brand_profile.defaulted} past defaults"

        if brand_profile.average_days_to_pay > 30:
            factors["slow_payer"] = f"Brand pays avg {brand_profile.average_days_to_pay:.0f} days late"

        # Invoice specific
        if invoice.invoice_amount > 50000:
            factors["high_amount"] = "Invoice amount exceeds $50,000"

        if features["days_until_due"] < 14:
            factors["short_term"] = "Less than 14 days until due date"

        if not invoice.contract_url:
            factors["no_contract"] = "No contract document provided"

        return factors

    def _calculate_advance_rate(
        self,
        risk_score: int,
        risk_level: RiskLevelEnum
    ) -> float:
        """Calculate recommended advance rate based on risk."""
        # Base rates by risk level
        base_rates = {
            RiskLevelEnum.LOW: 0.95,
            RiskLevelEnum.MEDIUM: 0.90,
            RiskLevelEnum.HIGH: 0.85,
            RiskLevelEnum.VERY_HIGH: 0.80
        }

        base_rate = base_rates.get(risk_level, 0.80)

        # Fine-tune based on exact score
        if risk_level == RiskLevelEnum.LOW:
            # 85-100: 0.90 to 0.95
            rate = 0.90 + (risk_score - 85) / 15 * 0.05
        elif risk_level == RiskLevelEnum.MEDIUM:
            # 70-84: 0.85 to 0.90
            rate = 0.85 + (risk_score - 70) / 15 * 0.05
        elif risk_level == RiskLevelEnum.HIGH:
            # 60-69: 0.80 to 0.85
            rate = 0.80 + (risk_score - 60) / 10 * 0.05
        else:
            # Below 60: 0.80 (minimum)
            rate = 0.80

        return round(max(settings.MIN_ADVANCE_RATE, min(settings.MAX_ADVANCE_RATE, rate)), 2)
