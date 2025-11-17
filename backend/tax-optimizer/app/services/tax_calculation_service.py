"""
Tax calculation service for deductions and estimates.
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.models import (
    Expense, ExpenseCategoryEnum, TaxDeduction,
    QuarterlyTaxEstimate, HomeOfficeDeduction
)
from app.core.config import settings


class TaxCalculationService:
    """Service for tax calculations and deductions."""

    def __init__(self, db: Session):
        self.db = db

    async def calculate_deductions(
        self,
        creator_id: int,
        tax_year: int
    ) -> Dict[str, Any]:
        """
        Calculate all deductions for a creator for a tax year.

        Args:
            creator_id: Creator ID
            tax_year: Tax year

        Returns:
            Dictionary with deduction breakdown
        """
        # Get all deductible expenses
        expenses = self.db.query(Expense).filter(
            Expense.creator_id == creator_id,
            Expense.tax_year == tax_year,
            Expense.deductible == True
        ).all()

        # Group by category
        deductions_by_category = {}

        for category in ExpenseCategoryEnum:
            category_expenses = [
                e for e in expenses
                if e.category == category
            ]

            if not category_expenses:
                continue

            total = sum(
                e.amount * (e.deduction_percentage / 100.0)
                for e in category_expenses
            )

            deductions_by_category[category.value] = {
                "total": total,
                "count": len(category_expenses),
                "expenses": [
                    {
                        "id": e.id,
                        "amount": e.amount,
                        "description": e.description,
                        "date": e.expense_date.isoformat()
                    }
                    for e in category_expenses
                ]
            }

            # Save to database
            deduction = TaxDeduction(
                creator_id=creator_id,
                tax_year=tax_year,
                category=category,
                total_amount=sum(e.amount for e in category_expenses),
                deductible_amount=total,
                expense_count=len(category_expenses)
            )
            self.db.add(deduction)

        self.db.commit()

        # Calculate totals
        total_deductions = sum(
            d["total"] for d in deductions_by_category.values()
        )

        return {
            "tax_year": tax_year,
            "total_deductions": total_deductions,
            "by_category": deductions_by_category,
            "standard_deduction": 13850,  # 2024 single filer
            "recommendation": (
                "itemize" if total_deductions > 13850 else "standard"
            )
        }

    async def calculate_quarterly_estimate(
        self,
        creator_id: int,
        year: int,
        quarter: int
    ) -> QuarterlyTaxEstimate:
        """
        Calculate quarterly tax estimate.

        Args:
            creator_id: Creator ID
            year: Tax year
            quarter: Quarter (1-4)

        Returns:
            QuarterlyTaxEstimate object
        """
        # Get quarter date range
        quarter_ranges = {
            1: (date(year, 1, 1), date(year, 3, 31)),
            2: (date(year, 4, 1), date(year, 6, 30)),
            3: (date(year, 7, 1), date(year, 9, 30)),
            4: (date(year, 10, 1), date(year, 12, 31)),
        }
        start_date, end_date = quarter_ranges[quarter]

        # Get gross income for quarter (from attribution engine)
        # This would query the income table from attribution engine
        # For now, we'll use a placeholder
        gross_income = 0.0  # TODO: Query from attribution engine

        # Get expenses for quarter
        expenses = self.db.query(Expense).filter(
            Expense.creator_id == creator_id,
            Expense.expense_date >= start_date,
            Expense.expense_date <= end_date,
            Expense.deductible == True
        ).all()

        total_expenses = sum(
            e.amount * (e.deduction_percentage / 100.0)
            for e in expenses
        )

        # Calculate net income
        net_income = gross_income - total_expenses

        # Calculate federal income tax (simplified)
        federal_tax = self._calculate_federal_tax(net_income)

        # Calculate self-employment tax
        se_tax = net_income * settings.SELF_EMPLOYMENT_TAX_RATE

        # State tax (placeholder - would vary by state)
        state_tax = net_income * 0.05  # 5% example

        # Total tax owed
        total_tax = federal_tax + se_tax + state_tax

        # Quarterly payment due dates
        due_dates = {
            1: date(year, 4, 15),
            2: date(year, 6, 15),
            3: date(year, 9, 15),
            4: date(year + 1, 1, 15),
        }

        # Create estimate
        estimate = QuarterlyTaxEstimate(
            creator_id=creator_id,
            tax_year=year,
            quarter=quarter,
            gross_income=gross_income,
            net_income=net_income,
            federal_income_tax=federal_tax,
            self_employment_tax=se_tax,
            state_tax=state_tax,
            total_tax_owed=total_tax,
            total_deductions=total_expenses,
            due_date=due_dates[quarter],
            calculation_details={
                "expense_count": len(expenses),
                "tax_bracket": settings.DEFAULT_TAX_BRACKET,
                "se_tax_rate": settings.SELF_EMPLOYMENT_TAX_RATE
            }
        )

        self.db.add(estimate)
        self.db.commit()
        self.db.refresh(estimate)

        return estimate

    def _calculate_federal_tax(self, income: float) -> float:
        """
        Calculate federal income tax using tax brackets.

        Args:
            income: Taxable income

        Returns:
            Federal tax amount
        """
        # 2024 tax brackets (single filer)
        brackets = [
            (11000, 0.10),
            (44725, 0.12),
            (95375, 0.22),
            (182100, 0.24),
            (231250, 0.32),
            (578125, 0.35),
            (float('inf'), 0.37)
        ]

        tax = 0.0
        previous_limit = 0

        for limit, rate in brackets:
            if income <= previous_limit:
                break

            taxable_in_bracket = min(income, limit) - previous_limit
            tax += taxable_in_bracket * rate
            previous_limit = limit

        return tax

    async def calculate_home_office_deduction(
        self,
        creator_id: int,
        tax_year: int,
        method: str = "simplified",
        square_feet: Optional[float] = None,
        home_area_total: Optional[float] = None,
        office_area: Optional[float] = None,
        expenses: Optional[Dict[str, float]] = None
    ) -> HomeOfficeDeduction:
        """
        Calculate home office deduction.

        Args:
            creator_id: Creator ID
            tax_year: Tax year
            method: "simplified" or "actual"
            square_feet: Office square feet (simplified method)
            home_area_total: Total home sq ft (actual method)
            office_area: Office sq ft (actual method)
            expenses: Dict of home expenses (actual method)

        Returns:
            HomeOfficeDeduction object
        """
        if method == "simplified":
            # Simplified method: $5 per square foot, max 300 sq ft
            sq_ft = min(square_feet or 0, 300)
            deduction = sq_ft * 5.0

            home_office = HomeOfficeDeduction(
                creator_id=creator_id,
                tax_year=tax_year,
                method="simplified",
                square_feet=sq_ft,
                total_deduction=deduction
            )

        else:  # actual method
            # Calculate business percentage
            business_pct = (office_area / home_area_total) if home_area_total else 0

            # Apply business percentage to all home expenses
            expenses = expenses or {}

            deductible_mortgage = expenses.get('mortgage_interest', 0) * business_pct
            deductible_tax = expenses.get('property_tax', 0) * business_pct
            deductible_utilities = expenses.get('utilities', 0) * business_pct
            deductible_insurance = expenses.get('insurance', 0) * business_pct
            deductible_repairs = expenses.get('repairs', 0) * business_pct
            deductible_depreciation = expenses.get('depreciation', 0) * business_pct

            total_deduction = (
                deductible_mortgage +
                deductible_tax +
                deductible_utilities +
                deductible_insurance +
                deductible_repairs +
                deductible_depreciation
            )

            home_office = HomeOfficeDeduction(
                creator_id=creator_id,
                tax_year=tax_year,
                method="actual",
                home_area_total=home_area_total,
                office_area=office_area,
                business_percentage=business_pct * 100,
                mortgage_interest=deductible_mortgage,
                property_tax=deductible_tax,
                utilities=deductible_utilities,
                insurance=deductible_insurance,
                repairs=deductible_repairs,
                depreciation=deductible_depreciation,
                total_deduction=total_deduction
            )

        self.db.add(home_office)
        self.db.commit()
        self.db.refresh(home_office)

        return home_office
