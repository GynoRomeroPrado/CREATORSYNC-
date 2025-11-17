"""
Expense categorization service using ML.
"""
from typing import Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
import os

from app.db.models import ExpenseCategoryEnum
from app.core.config import settings


class ExpenseCategorizerService:
    """Service for automatically categorizing expenses using ML."""

    def __init__(self):
        self.model_path = os.path.join(
            settings.MODEL_PATH,
            "categorizer_model.pkl"
        )
        self.model = self._load_or_create_model()

    def _load_or_create_model(self) -> Pipeline:
        """Load existing model or create new one."""
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)

        # Create new model pipeline
        model = Pipeline([
            ('tfidf', TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words='english'
            )),
            ('clf', MultinomialNB(alpha=0.1))
        ])

        return model

    async def categorize_expense(
        self,
        description: str,
        vendor: Optional[str] = None,
        amount: Optional[float] = None,
        ocr_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Categorize an expense based on description and other data.

        Args:
            description: Expense description
            vendor: Vendor name
            amount: Expense amount
            ocr_text: Full OCR text from receipt

        Returns:
            Dictionary with category and confidence
        """
        # Combine all text features
        text_features = self._build_text_features(
            description, vendor, ocr_text
        )

        # Use rule-based categorization if model not trained
        if not hasattr(self.model.named_steps['clf'], 'classes_'):
            category = self._rule_based_categorization(text_features, amount)
            return {
                "category": category,
                "confidence": 0.6,  # Medium confidence for rule-based
                "method": "rule_based"
            }

        # Predict with ML model
        try:
            prediction = self.model.predict([text_features])[0]
            probabilities = self.model.predict_proba([text_features])[0]
            confidence = max(probabilities)

            return {
                "category": prediction,
                "confidence": float(confidence),
                "method": "ml_model",
                "all_predictions": {
                    cat: float(prob)
                    for cat, prob in zip(
                        self.model.named_steps['clf'].classes_,
                        probabilities
                    )
                }
            }
        except Exception as e:
            # Fallback to rule-based
            category = self._rule_based_categorization(text_features, amount)
            return {
                "category": category,
                "confidence": 0.5,
                "method": "rule_based_fallback",
                "error": str(e)
            }

    def _build_text_features(
        self,
        description: str,
        vendor: Optional[str],
        ocr_text: Optional[str]
    ) -> str:
        """Combine text features for classification."""
        features = [description.lower()]

        if vendor:
            features.append(vendor.lower())

        if ocr_text:
            # Include relevant parts of OCR text
            features.append(ocr_text[:200].lower())

        return " ".join(features)

    def _rule_based_categorization(
        self,
        text: str,
        amount: Optional[float] = None
    ) -> str:
        """
        Rule-based categorization using keywords.

        Args:
            text: Combined text features
            amount: Expense amount

        Returns:
            Category string
        """
        text_lower = text.lower()

        # Equipment keywords
        if any(word in text_lower for word in [
            'camera', 'lens', 'microphone', 'mic', 'computer', 'laptop',
            'iphone', 'ipad', 'monitor', 'keyboard', 'mouse', 'tripod',
            'lighting', 'lights', 'audio', 'video', 'equipment'
        ]):
            return ExpenseCategoryEnum.EQUIPMENT.value

        # Software keywords
        if any(word in text_lower for word in [
            'adobe', 'subscription', 'software', 'app', 'saas',
            'photoshop', 'premiere', 'final cut', 'canva', 'notion',
            'spotify', 'music', 'cloud', 'storage', 'hosting'
        ]):
            return ExpenseCategoryEnum.SOFTWARE.value

        # Travel keywords
        if any(word in text_lower for word in [
            'airline', 'flight', 'hotel', 'airbnb', 'uber', 'lyft',
            'rental car', 'parking', 'travel', 'airport', 'taxi'
        ]):
            return ExpenseCategoryEnum.TRAVEL.value

        # Meals keywords
        if any(word in text_lower for word in [
            'restaurant', 'cafe', 'coffee', 'starbucks', 'food',
            'lunch', 'dinner', 'breakfast', 'meal', 'catering'
        ]):
            return ExpenseCategoryEnum.MEALS.value

        # Utilities keywords
        if any(word in text_lower for word in [
            'internet', 'wifi', 'phone', 'mobile', 'verizon',
            'at&t', 't-mobile', 'comcast', 'spectrum', 'utility'
        ]):
            return ExpenseCategoryEnum.UTILITIES.value

        # Advertising keywords
        if any(word in text_lower for word in [
            'facebook ads', 'google ads', 'instagram ads', 'tiktok ads',
            'advertising', 'promotion', 'marketing', 'sponsored'
        ]):
            return ExpenseCategoryEnum.ADVERTISING.value

        # Professional services
        if any(word in text_lower for word in [
            'accountant', 'lawyer', 'attorney', 'consultant',
            'tax preparation', 'legal', 'professional'
        ]):
            return ExpenseCategoryEnum.PROFESSIONAL_SERVICES.value

        # Education
        if any(word in text_lower for word in [
            'course', 'training', 'workshop', 'seminar', 'class',
            'education', 'udemy', 'coursera', 'masterclass'
        ]):
            return ExpenseCategoryEnum.EDUCATION.value

        # Insurance
        if 'insurance' in text_lower:
            return ExpenseCategoryEnum.INSURANCE.value

        # Home office (harder to detect, usually manual)
        if any(word in text_lower for word in [
            'home office', 'desk', 'chair', 'office furniture'
        ]):
            return ExpenseCategoryEnum.HOME_OFFICE.value

        # Default to supplies or other
        if amount and amount < 100:
            return ExpenseCategoryEnum.SUPPLIES.value

        return ExpenseCategoryEnum.OTHER.value

    def train_model(self, training_data: list[tuple[str, str]]):
        """
        Train the categorization model.

        Args:
            training_data: List of (text, category) tuples
        """
        if len(training_data) < 50:
            print("Not enough training data. Need at least 50 examples.")
            return

        texts, categories = zip(*training_data)

        # Train the model
        self.model.fit(texts, categories)

        # Save the model
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)

        print(f"Model trained on {len(training_data)} examples and saved.")
