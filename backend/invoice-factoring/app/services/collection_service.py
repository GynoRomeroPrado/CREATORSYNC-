"""
Collections service for overdue invoices.
"""
from typing import Dict, Any, List
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.db.models import (
    Invoice, CollectionAttempt, InvoiceStatusEnum
)
from app.core.config import settings


class CollectionService:
    """Service for collecting on invoices."""

    def __init__(self, db: Session):
        self.db = db

    async def check_overdue_invoices(self) -> List[Invoice]:
        """
        Check for overdue invoices and initiate collections.

        Returns:
            List of overdue invoices
        """
        # Get funded invoices past due date
        overdue_invoices = self.db.query(Invoice).filter(
            Invoice.status.in_([
                InvoiceStatusEnum.FUNDED,
                InvoiceStatusEnum.COLLECTING
            ]),
            Invoice.due_date < date.today()
        ).all()

        for invoice in overdue_invoices:
            if invoice.status == InvoiceStatusEnum.FUNDED:
                # First time overdue - start collection process
                invoice.status = InvoiceStatusEnum.COLLECTING
                self.db.commit()

            # Send collection reminders
            await self.send_collection_reminder(invoice.id)

        return overdue_invoices

    async def send_collection_reminder(
        self,
        invoice_id: int,
        method: str = "email"
    ) -> CollectionAttempt:
        """
        Send a collection reminder.

        Args:
            invoice_id: Invoice ID
            method: Communication method

        Returns:
            CollectionAttempt record
        """
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError("Invoice not found")

        # Get previous attempts
        previous_attempts = self.db.query(CollectionAttempt).filter(
            CollectionAttempt.invoice_id == invoice_id
        ).count()

        attempt_number = previous_attempts + 1

        # Determine message content based on attempt number
        message = self._get_collection_message(invoice, attempt_number)

        # Send email
        if method == "email" and invoice.brand_email:
            await self._send_email(
                to_email=invoice.brand_email,
                subject=f"Payment Reminder - Invoice #{invoice.invoice_number}",
                body=message
            )

        # Record attempt
        attempt = CollectionAttempt(
            invoice_id=invoice_id,
            attempt_number=attempt_number,
            method=method,
            sent_to=invoice.brand_email or invoice.brand_name,
            message_content=message
        )

        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)

        return attempt

    def _get_collection_message(
        self,
        invoice: Invoice,
        attempt_number: int
    ) -> str:
        """Generate collection message based on attempt number."""
        days_overdue = (date.today() - invoice.due_date).days

        if attempt_number == 1:
            # Friendly first reminder
            return f"""
Dear {invoice.brand_name},

This is a friendly reminder that Invoice #{invoice.invoice_number} for ${invoice.invoice_amount:.2f}
was due on {invoice.due_date.strftime('%Y-%m-%d')} and is now {days_overdue} days overdue.

Please process payment at your earliest convenience.

Original Invoice Amount: ${invoice.invoice_amount:.2f}
Due Date: {invoice.due_date.strftime('%Y-%m-%d')}
Days Overdue: {days_overdue}

If payment has already been sent, please disregard this notice.

Best regards,
CreatorSync Finance Team
            """.strip()

        elif attempt_number == 2:
            # Second reminder - more urgent
            return f"""
Dear {invoice.brand_name},

This is a second reminder regarding Invoice #{invoice.invoice_number} for ${invoice.invoice_amount:.2f},
which is now {days_overdue} days overdue.

Late fees may apply after 30 days.

Please contact us immediately if there are any issues with this invoice.

Original Invoice Amount: ${invoice.invoice_amount:.2f}
Due Date: {invoice.due_date.strftime('%Y-%m-%d')}
Days Overdue: {days_overdue}

Best regards,
CreatorSync Finance Team
            """.strip()

        else:
            # Final notice
            late_fee = invoice.late_fees or 0
            total_due = invoice.invoice_amount + late_fee

            return f"""
FINAL NOTICE

Dear {invoice.brand_name},

Invoice #{invoice.invoice_number} is now {days_overdue} days overdue.

Original Amount: ${invoice.invoice_amount:.2f}
Late Fees: ${late_fee:.2f}
Total Due: ${total_due:.2f}

Payment must be received within 7 days to avoid legal action.

Please contact us immediately to resolve this matter.

CreatorSync Legal Department
            """.strip()

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        body: str
    ):
        """Send email notification."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            print(f"Email would be sent to {to_email}: {subject}")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = settings.SMTP_USER
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()

            print(f"Collection email sent to {to_email}")

        except Exception as e:
            print(f"Failed to send email: {e}")

    async def schedule_collection_reminders(self):
        """
        Schedule collection reminders based on due dates.

        This would be run as a daily cron job.
        """
        today = date.today()

        # Get invoices approaching due date
        for days_before in settings.COLLECTION_REMINDER_DAYS:
            reminder_date = today + timedelta(days=days_before)

            invoices = self.db.query(Invoice).filter(
                Invoice.status == InvoiceStatusEnum.FUNDED,
                Invoice.due_date == reminder_date
            ).all()

            for invoice in invoices:
                await self.send_pre_due_reminder(invoice.id, days_before)

    async def send_pre_due_reminder(
        self,
        invoice_id: int,
        days_until_due: int
    ):
        """Send reminder before due date."""
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice or not invoice.brand_email:
            return

        message = f"""
Dear {invoice.brand_name},

This is a friendly reminder that Invoice #{invoice.invoice_number} for ${invoice.invoice_amount:.2f}
is due in {days_until_due} days on {invoice.due_date.strftime('%Y-%m-%d')}.

Please ensure payment is processed by the due date to avoid late fees.

Invoice Amount: ${invoice.invoice_amount:.2f}
Due Date: {invoice.due_date.strftime('%Y-%m-%d')}
Days Until Due: {days_until_due}

Best regards,
CreatorSync Finance Team
        """.strip()

        await self._send_email(
            to_email=invoice.brand_email,
            subject=f"Upcoming Payment - Invoice #{invoice.invoice_number}",
            body=message
        )

    async def escalate_to_legal(self, invoice_id: int) -> Dict[str, Any]:
        """
        Escalate invoice to legal collection.

        Args:
            invoice_id: Invoice ID

        Returns:
            Escalation details
        """
        invoice = self.db.query(Invoice).filter(
            Invoice.id == invoice_id
        ).first()

        if not invoice:
            raise ValueError("Invoice not found")

        days_overdue = (date.today() - invoice.due_date).days

        if days_overdue < 60:
            raise ValueError("Invoice must be at least 60 days overdue for legal escalation")

        # Mark as defaulted
        invoice.status = InvoiceStatusEnum.DEFAULTED

        # Record legal escalation attempt
        attempt = CollectionAttempt(
            invoice_id=invoice_id,
            attempt_number=999,  # Special number for legal
            method="legal",
            sent_to=invoice.brand_name,
            message_content="Escalated to legal collection"
        )

        self.db.add(attempt)
        self.db.commit()

        return {
            "invoice_id": invoice_id,
            "status": "escalated_to_legal",
            "days_overdue": days_overdue,
            "amount_owed": invoice.invoice_amount + (invoice.late_fees or 0),
            "next_steps": "Legal team will contact brand within 5 business days"
        }
