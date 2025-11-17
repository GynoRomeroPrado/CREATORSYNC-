"""
Attribution service for linking income to content using ML.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import joblib
import os

from app.db.models import Creator, Content, Income, Attribution
from app.core.config import settings


class AttributionService:
    """Service for income attribution to content."""

    def __init__(self, db: Session):
        self.db = db
        self.model_path = os.path.join(settings.MODEL_PATH, "attribution", "xgboost_model.pkl")
        self.scaler_path = os.path.join(settings.MODEL_PATH, "attribution", "scaler.pkl")
        self.model = self._load_or_create_model()
        self.scaler = self._load_or_create_scaler()

    def _load_or_create_model(self) -> XGBRegressor:
        """Load existing model or create new one."""
        if os.path.exists(self.model_path):
            return joblib.load(self.model_path)

        # Create new model with default parameters
        model = XGBRegressor(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42
        )
        return model

    def _load_or_create_scaler(self) -> StandardScaler:
        """Load existing scaler or create new one."""
        if os.path.exists(self.scaler_path):
            return joblib.load(self.scaler_path)

        return StandardScaler()

    async def run_attribution(
        self,
        creator_id: int,
        income_ids: Optional[List[int]] = None
    ) -> List[Attribution]:
        """
        Run attribution analysis for a creator.

        Args:
            creator_id: Creator ID
            income_ids: Optional list of specific income IDs to attribute

        Returns:
            List of created Attribution records
        """
        # Get unattributed income
        income_query = self.db.query(Income).filter(
            Income.creator_id == creator_id,
            Income.is_reconciled == False
        )

        if income_ids:
            income_query = income_query.filter(Income.id.in_(income_ids))

        income_records = income_query.all()

        if not income_records:
            return []

        attributions = []

        for income in income_records:
            # Find content published around the income period
            content_candidates = self._get_content_candidates(
                creator_id=creator_id,
                income=income
            )

            if not content_candidates:
                # Create attribution without specific content (platform-level)
                attribution = Attribution(
                    creator_id=creator_id,
                    income_id=income.id,
                    content_id=None,
                    attributed_amount=income.amount,
                    confidence_score=0.5,  # Medium confidence
                    attribution_method="platform_aggregate",
                    model_version=settings.ATTRIBUTION_MODEL_VERSION
                )
                self.db.add(attribution)
                attributions.append(attribution)
                continue

            # Use ML model to attribute income to content
            content_attributions = self._attribute_income_to_content(
                income=income,
                content_candidates=content_candidates
            )

            for content_id, amount, confidence in content_attributions:
                attribution = Attribution(
                    creator_id=creator_id,
                    income_id=income.id,
                    content_id=content_id,
                    attributed_amount=amount,
                    confidence_score=confidence,
                    attribution_method="ml_model",
                    model_version=settings.ATTRIBUTION_MODEL_VERSION
                )
                self.db.add(attribution)
                attributions.append(attribution)

            # Mark income as reconciled
            income.is_reconciled = True

        self.db.commit()
        return attributions

    def _get_content_candidates(
        self,
        creator_id: int,
        income: Income
    ) -> List[Content]:
        """
        Get content that could have generated this income.

        Args:
            creator_id: Creator ID
            income: Income record

        Returns:
            List of candidate Content records
        """
        # Define lookback period based on income type
        if income.income_type.value == "ad_revenue":
            # Ad revenue typically reflects views from 30-60 days prior
            lookback_days = 60
        elif income.income_type.value == "brand_deal":
            # Brand deals reflect specific campaign content
            lookback_days = 90
        else:
            lookback_days = 30

        start_date = income.income_date - timedelta(days=lookback_days)

        # Get content from the same platform published before income date
        from app.db.models import PlatformConnection
        content = self.db.query(Content).join(PlatformConnection).filter(
            Content.creator_id == creator_id,
            PlatformConnection.platform == income.platform,
            Content.published_at >= start_date,
            Content.published_at <= income.income_date
        ).all()

        return content

    def _attribute_income_to_content(
        self,
        income: Income,
        content_candidates: List[Content]
    ) -> List[tuple[int, float, float]]:
        """
        Attribute income to specific content using ML model.

        Args:
            income: Income record
            content_candidates: List of candidate content

        Returns:
            List of (content_id, attributed_amount, confidence_score) tuples
        """
        if not content_candidates:
            return []

        # Extract features for each content piece
        features_list = []
        content_ids = []

        for content in content_candidates:
            features = self._extract_features(content, income)
            features_list.append(features)
            content_ids.append(content.id)

        # Create DataFrame
        df = pd.DataFrame(features_list)

        # Scale features
        X = self.scaler.fit_transform(df)

        # Predict attribution scores (relative weights)
        try:
            scores = self.model.predict(X)
        except:
            # If model not trained, use simple heuristic based on views
            scores = np.array([c.views for c in content_candidates])

        # Normalize scores to sum to 1
        scores = np.maximum(scores, 0)  # Ensure non-negative
        total_score = scores.sum()

        if total_score == 0:
            # Equal distribution if all scores are 0
            scores = np.ones(len(scores)) / len(scores)
        else:
            scores = scores / total_score

        # Calculate attributed amounts and confidence
        results = []
        for i, content_id in enumerate(content_ids):
            attributed_amount = income.amount * scores[i]
            confidence_score = min(scores[i] * 2, 1.0)  # Scale to 0-1

            # Only include if attributed amount is significant
            if attributed_amount > 0.01:  # At least 1 cent
                results.append((content_id, attributed_amount, confidence_score))

        return results

    def _extract_features(self, content: Content, income: Income) -> Dict[str, Any]:
        """
        Extract features for ML model.

        Args:
            content: Content record
            income: Income record

        Returns:
            Dictionary of features
        """
        # Time difference between content and income
        time_diff_days = (income.income_date - content.published_at).days

        # Engagement metrics
        engagement_rate = content.engagement_rate or 0.0
        views = content.views or 0
        likes = content.likes or 0
        comments = content.comments or 0

        # Watch time (if available)
        watch_time = content.watch_time_minutes or 0

        return {
            "time_diff_days": time_diff_days,
            "views": views,
            "likes": likes,
            "comments": comments,
            "engagement_rate": engagement_rate,
            "watch_time_minutes": watch_time,
            "content_type_video": 1 if content.content_type.value == "video" else 0,
            "content_type_short": 1 if content.content_type.value == "short" else 0,
            "content_type_livestream": 1 if content.content_type.value == "livestream" else 0,
        }

    def train_model(self, creator_id: Optional[int] = None):
        """
        Train attribution model on historical data.

        Args:
            creator_id: Optional creator ID to train on specific creator's data
        """
        # Get historical attributions with manual verification
        query = self.db.query(Attribution).filter(
            Attribution.confidence_score > 0.8  # Only high-confidence data
        )

        if creator_id:
            query = query.filter(Attribution.creator_id == creator_id)

        attributions = query.all()

        if len(attributions) < 100:
            print("Not enough training data. Need at least 100 verified attributions.")
            return

        # Prepare training data
        X_list = []
        y_list = []

        for attr in attributions:
            if not attr.content_id:
                continue

            content = self.db.query(Content).get(attr.content_id)
            income = self.db.query(Income).get(attr.income_id)

            if not content or not income:
                continue

            features = self._extract_features(content, income)
            X_list.append(features)
            y_list.append(attr.attributed_amount / income.amount)  # Relative amount

        df_X = pd.DataFrame(X_list)
        y = np.array(y_list)

        # Scale features
        X_scaled = self.scaler.fit_transform(df_X)

        # Train model
        self.model.fit(X_scaled, y)

        # Save model and scaler
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)

        print(f"Model trained on {len(attributions)} examples and saved.")
