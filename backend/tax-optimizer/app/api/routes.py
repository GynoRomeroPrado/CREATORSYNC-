"""
API routes for Tax Optimizer.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import os
import shutil

from app.db.base import get_db
from app.db.models import Expense, BankAccount, TaxDeduction, QuarterlyTaxEstimate, TaxForm
from app.api.schemas import *
from app.services.ocr_service import OCRService
from app.services.categorizer_service import ExpenseCategorizerService
from app.services.tax_calculation_service import TaxCalculationService
from app.services.tax_form_generator import TaxFormGenerator
from app.core.config import settings

# Routers
expense_router = APIRouter()
bank_router = APIRouter()
deduction_router = APIRouter()
quarterly_router = APIRouter()
form_router = APIRouter()
dashboard_router = APIRouter()


# ============================================================================
# EXPENSE ROUTES
# ============================================================================

@expense_router.post("/", response_model=ExpenseResponse)
async def create_expense(
    creator_id: int,
    expense: ExpenseCreate,
    db: Session = Depends(get_db)
):
    """Create a new expense."""
    db_expense = Expense(
        creator_id=creator_id,
        tax_year=expense.expense_date.year,
        **expense.model_dump()
    )
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense


@expense_router.post("/upload-receipt", response_model=ReceiptUploadResponse)
async def upload_receipt(
    creator_id: int = Form(...),
    expense_date: date = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload and process a receipt."""
    # Save file
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, f"{creator_id}_{datetime.now().timestamp()}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Process with OCR
    ocr_service = OCRService()
    ocr_result = await ocr_service.process_receipt(file_path)

    # Categorize expense
    categorizer = ExpenseCategorizerService()
    category_result = await categorizer.categorize_expense(
        description=ocr_result["structured_data"].get("vendor", "Unknown"),
        vendor=ocr_result["structured_data"].get("vendor"),
        amount=ocr_result["structured_data"].get("total_amount"),
        ocr_text=ocr_result["raw_text"]
    )

    # Create expense
    expense = Expense(
        creator_id=creator_id,
        amount=ocr_result["structured_data"].get("total_amount") or 0.0,
        category=category_result["category"],
        description=ocr_result["structured_data"].get("vendor") or "Unknown",
        vendor=ocr_result["structured_data"].get("vendor"),
        expense_date=expense_date,
        receipt_url=file_path,
        receipt_filename=file.filename,
        ocr_text=ocr_result["raw_text"],
        ocr_confidence=ocr_result["confidence"],
        ocr_data=ocr_result["structured_data"],
        auto_categorized=True,
        category_confidence=category_result["confidence"],
        processing_status="completed",
        tax_year=expense_date.year
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return ReceiptUploadResponse(
        expense_id=expense.id,
        filename=file.filename,
        ocr_text=ocr_result["raw_text"],
        extracted_data=ocr_result["structured_data"],
        suggested_category=category_result["category"],
        category_confidence=category_result["confidence"]
    )


@expense_router.get("/creator/{creator_id}", response_model=List[ExpenseResponse])
async def list_expenses(
    creator_id: int,
    tax_year: Optional[int] = None,
    category: Optional[ExpenseCategoryEnum] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List expenses for a creator."""
    query = db.query(Expense).filter(Expense.creator_id == creator_id)

    if tax_year:
        query = query.filter(Expense.tax_year == tax_year)
    if category:
        query = query.filter(Expense.category == category)

    expenses = query.order_by(Expense.expense_date.desc()).offset(skip).limit(limit).all()
    return expenses


@expense_router.patch("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    category: Optional[ExpenseCategoryEnum] = None,
    deductible: Optional[bool] = None,
    deduction_percentage: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Update an expense."""
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if category:
        expense.category = category
        expense.manual_category_override = True
    if deductible is not None:
        expense.deductible = deductible
    if deduction_percentage is not None:
        expense.deduction_percentage = deduction_percentage

    db.commit()
    db.refresh(expense)
    return expense


# ============================================================================
# BANK ACCOUNT ROUTES
# ============================================================================

@bank_router.post("/connect")
async def connect_bank_account(
    creator_id: int,
    data: BankAccountConnect,
    db: Session = Depends(get_db)
):
    """Connect a bank account via Plaid."""
    # This would exchange public_token for access_token via Plaid API
    # For now, simplified implementation
    return {
        "status": "success",
        "message": "Bank account connected (Plaid integration pending)"
    }


@bank_router.get("/creator/{creator_id}", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    creator_id: int,
    db: Session = Depends(get_db)
):
    """List connected bank accounts."""
    accounts = db.query(BankAccount).filter(
        BankAccount.creator_id == creator_id,
        BankAccount.is_active == True
    ).all()
    return accounts


# ============================================================================
# DEDUCTION ROUTES
# ============================================================================

@deduction_router.post("/calculate/{creator_id}", response_model=DeductionSummary)
async def calculate_deductions(
    creator_id: int,
    tax_year: int,
    db: Session = Depends(get_db)
):
    """Calculate deductions for a tax year."""
    tax_service = TaxCalculationService(db)
    deductions = await tax_service.calculate_deductions(creator_id, tax_year)
    return deductions


@deduction_router.get("/creator/{creator_id}", response_model=List[TaxDeductionResponse])
async def get_deductions(
    creator_id: int,
    tax_year: int,
    db: Session = Depends(get_db)
):
    """Get calculated deductions."""
    deductions = db.query(TaxDeduction).filter(
        TaxDeduction.creator_id == creator_id,
        TaxDeduction.tax_year == tax_year
    ).all()
    return deductions


@deduction_router.post("/home-office/{creator_id}", response_model=HomeOfficeResponse)
async def calculate_home_office(
    creator_id: int,
    tax_year: int,
    data: HomeOfficeRequest,
    db: Session = Depends(get_db)
):
    """Calculate home office deduction."""
    tax_service = TaxCalculationService(db)
    deduction = await tax_service.calculate_home_office_deduction(
        creator_id=creator_id,
        tax_year=tax_year,
        method=data.method,
        square_feet=data.square_feet,
        home_area_total=data.home_area_total,
        office_area=data.office_area,
        expenses=data.expenses
    )
    return deduction


# ============================================================================
# QUARTERLY TAX ROUTES
# ============================================================================

@quarterly_router.post("/estimate/{creator_id}", response_model=QuarterlyEstimateResponse)
async def calculate_quarterly_estimate(
    creator_id: int,
    year: int,
    quarter: int,
    db: Session = Depends(get_db)
):
    """Calculate quarterly tax estimate."""
    if quarter not in [1, 2, 3, 4]:
        raise HTTPException(status_code=400, detail="Quarter must be 1-4")

    tax_service = TaxCalculationService(db)
    estimate = await tax_service.calculate_quarterly_estimate(
        creator_id, year, quarter
    )
    return estimate


@quarterly_router.get("/creator/{creator_id}", response_model=List[QuarterlyEstimateResponse])
async def get_quarterly_estimates(
    creator_id: int,
    year: int,
    db: Session = Depends(get_db)
):
    """Get quarterly estimates for a year."""
    estimates = db.query(QuarterlyTaxEstimate).filter(
        QuarterlyTaxEstimate.creator_id == creator_id,
        QuarterlyTaxEstimate.tax_year == year
    ).order_by(QuarterlyTaxEstimate.quarter).all()
    return estimates


# ============================================================================
# TAX FORM ROUTES
# ============================================================================

@form_router.post("/1099-nec/{creator_id}", response_model=TaxFormResponse)
async def generate_1099_nec(
    creator_id: int,
    tax_year: int,
    data: TaxForm1099Request,
    db: Session = Depends(get_db)
):
    """Generate Form 1099-NEC."""
    generator = TaxFormGenerator(db)
    form = await generator.generate_1099_nec(
        creator_id=creator_id,
        tax_year=tax_year,
        payer_info=data.payer_info,
        recipient_info=data.recipient_info,
        nonemployee_compensation=data.nonemployee_compensation
    )
    return form


@form_router.post("/schedule-c/{creator_id}", response_model=TaxFormResponse)
async def generate_schedule_c(
    creator_id: int,
    tax_year: int,
    data: TaxFormScheduleCRequest,
    db: Session = Depends(get_db)
):
    """Generate Schedule C."""
    generator = TaxFormGenerator(db)
    form = await generator.generate_schedule_c(
        creator_id=creator_id,
        tax_year=tax_year,
        business_info=data.business_info,
        income_data=data.income_data,
        expense_data=data.expense_data
    )
    return form


@form_router.post("/w9/{creator_id}", response_model=TaxFormResponse)
async def generate_w9(
    creator_id: int,
    data: TaxFormW9Request,
    db: Session = Depends(get_db)
):
    """Generate Form W-9."""
    generator = TaxFormGenerator(db)
    form = await generator.generate_w9(
        creator_id=creator_id,
        taxpayer_info=data.taxpayer_info
    )
    return form


@form_router.get("/creator/{creator_id}", response_model=List[TaxFormResponse])
async def list_tax_forms(
    creator_id: int,
    tax_year: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List generated tax forms."""
    query = db.query(TaxForm).filter(TaxForm.creator_id == creator_id)

    if tax_year:
        query = query.filter(TaxForm.tax_year == tax_year)

    forms = query.order_by(TaxForm.generated_at.desc()).all()
    return forms


# ============================================================================
# DASHBOARD ROUTE
# ============================================================================

@dashboard_router.get("/creator/{creator_id}", response_model=TaxDashboard)
async def get_tax_dashboard(
    creator_id: int,
    tax_year: int,
    db: Session = Depends(get_db)
):
    """Get tax dashboard overview."""
    from sqlalchemy import func

    # Get YTD expenses
    expenses = db.query(Expense).filter(
        Expense.creator_id == creator_id,
        Expense.tax_year == tax_year
    ).all()

    ytd_expenses = sum(e.amount for e in expenses)
    ytd_deductions = sum(
        e.amount * (e.deduction_percentage / 100.0)
        for e in expenses if e.deductible
    )

    # Expense summary by category
    expense_summary = {}
    for category in ExpenseCategoryEnum:
        cat_expenses = [e for e in expenses if e.category == category]
        if cat_expenses:
            expense_summary[category.value] = sum(e.amount for e in cat_expenses)

    # Get next quarterly payment
    next_estimate = db.query(QuarterlyTaxEstimate).filter(
        QuarterlyTaxEstimate.creator_id == creator_id,
        QuarterlyTaxEstimate.tax_year == tax_year,
        QuarterlyTaxEstimate.paid == False,
        QuarterlyTaxEstimate.due_date >= date.today()
    ).order_by(QuarterlyTaxEstimate.due_date).first()

    # Get top deductions
    top_deductions = db.query(TaxDeduction).filter(
        TaxDeduction.creator_id == creator_id,
        TaxDeduction.tax_year == tax_year
    ).order_by(TaxDeduction.deductible_amount.desc()).limit(5).all()

    return TaxDashboard(
        creator_id=creator_id,
        tax_year=tax_year,
        ytd_income=0.0,  # Would query from attribution engine
        ytd_expenses=ytd_expenses,
        ytd_deductions=ytd_deductions,
        estimated_tax_owed=next_estimate.total_tax_owed if next_estimate else 0.0,
        next_payment_due=next_estimate.due_date if next_estimate else None,
        next_payment_amount=next_estimate.total_tax_owed if next_estimate else None,
        expense_summary=expense_summary,
        top_deductions=top_deductions
    )
