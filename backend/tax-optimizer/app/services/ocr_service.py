"""
OCR service for receipt processing.
"""
import os
from typing import Dict, Any, Optional
from PIL import Image
import pytesseract
import cv2
import numpy as np
from datetime import datetime
import re


class OCRService:
    """Service for extracting text from receipts using OCR."""

    def __init__(self):
        self.confidence_threshold = 0.7

    async def process_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        Process a receipt image and extract text.

        Args:
            image_path: Path to receipt image

        Returns:
            Dictionary with extracted data
        """
        # Preprocess image
        processed_image = self._preprocess_image(image_path)

        # Extract text with Tesseract
        ocr_data = pytesseract.image_to_data(
            processed_image,
            output_type=pytesseract.Output.DICT
        )

        # Get full text
        text = pytesseract.image_to_string(processed_image)

        # Extract structured data
        structured_data = self._extract_structured_data(text, ocr_data)

        return {
            "raw_text": text,
            "confidence": self._calculate_confidence(ocr_data),
            "structured_data": structured_data,
            "ocr_metadata": {
                "word_count": len(ocr_data['text']),
                "processed_at": datetime.utcnow().isoformat()
            }
        }

    def _preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR results.

        Args:
            image_path: Path to image

        Returns:
            Processed image as numpy array
        """
        # Read image
        img = cv2.imread(image_path)

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply thresholding
        _, thresh = cv2.threshold(
            gray, 0, 255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        # Denoise
        denoised = cv2.fastNlMeansDenoising(thresh)

        # Deskew if needed
        deskewed = self._deskew_image(denoised)

        return deskewed

    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew tilted image."""
        coords = np.column_stack(np.where(image > 0))
        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )

        return rotated

    def _calculate_confidence(self, ocr_data: Dict) -> float:
        """Calculate average OCR confidence."""
        confidences = [
            float(conf) for conf in ocr_data['conf']
            if conf != '-1'
        ]

        if not confidences:
            return 0.0

        return sum(confidences) / len(confidences) / 100.0

    def _extract_structured_data(
        self,
        text: str,
        ocr_data: Dict
    ) -> Dict[str, Any]:
        """
        Extract structured data from OCR text.

        Args:
            text: Full OCR text
            ocr_data: Detailed OCR data from Tesseract

        Returns:
            Structured data dictionary
        """
        data = {
            "total_amount": self._extract_total(text),
            "date": self._extract_date(text),
            "vendor": self._extract_vendor(text),
            "items": self._extract_items(text),
            "payment_method": self._extract_payment_method(text)
        }

        return data

    def _extract_total(self, text: str) -> Optional[float]:
        """Extract total amount from receipt text."""
        # Common patterns for total
        patterns = [
            r'total[\s:]*\$?\s*(\d+\.\d{2})',
            r'amount[\s:]*\$?\s*(\d+\.\d{2})',
            r'grand total[\s:]*\$?\s*(\d+\.\d{2})',
        ]

        text_lower = text.lower()

        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return float(match.group(1))
                except:
                    continue

        # Fallback: find largest dollar amount
        amounts = re.findall(r'\$?\s*(\d+\.\d{2})', text)
        if amounts:
            return max(float(amt) for amt in amounts)

        return None

    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date from receipt text."""
        # Common date patterns
        patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}',
        ]

        text_lower = text.lower()

        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_vendor(self, text: str) -> Optional[str]:
        """Extract vendor/merchant name from receipt."""
        # Usually in first few lines
        lines = text.split('\n')

        # Get first non-empty line
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) > 3:
                # Clean up common receipt header text
                line = re.sub(r'receipt|invoice|bill', '', line, flags=re.IGNORECASE)
                line = line.strip()
                if line:
                    return line

        return None

    def _extract_items(self, text: str) -> list[Dict[str, Any]]:
        """Extract line items from receipt."""
        items = []

        # Pattern for line items: description + amount
        pattern = r'(.+?)\s+\$?\s*(\d+\.\d{2})'

        matches = re.finditer(pattern, text)

        for match in matches:
            description = match.group(1).strip()
            amount = float(match.group(2))

            # Filter out likely totals/subtotals
            if not any(word in description.lower() for word in ['total', 'subtotal', 'tax']):
                items.append({
                    "description": description,
                    "amount": amount
                })

        return items

    def _extract_payment_method(self, text: str) -> Optional[str]:
        """Extract payment method."""
        text_lower = text.lower()

        if 'visa' in text_lower:
            return 'visa'
        elif 'mastercard' in text_lower or 'master card' in text_lower:
            return 'mastercard'
        elif 'amex' in text_lower or 'american express' in text_lower:
            return 'amex'
        elif 'cash' in text_lower:
            return 'cash'
        elif 'debit' in text_lower:
            return 'debit'

        return None


class AWSTextractService:
    """Alternative OCR using AWS Textract (more accurate but costs $)."""

    def __init__(self):
        self.client = None  # Would initialize boto3 client

    async def process_receipt(self, image_path: str) -> Dict[str, Any]:
        """
        Process receipt using AWS Textract.

        Args:
            image_path: Path to receipt image

        Returns:
            Extracted data
        """
        # This would use boto3 to call AWS Textract
        # Implementation would be similar to OCRService
        # but using AWS Textract API
        raise NotImplementedError("AWS Textract integration pending")
