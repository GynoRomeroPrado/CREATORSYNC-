"""
Income forecasting service using Prophet.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import pandas as pd
from prophet import Prophet

from app.db.models import Creator, Income, ForecastData, PlatformEnum, IncomeTypeEnum
from app.core.config import settings
from app.api.schemas import ForecastResponse, ForecastDataPoint


class ForecastService:
    """Service for income forecasting using Facebook Prophet."""

    def __init__(self, db: Session):
        self.db = db

    async def generate_forecast(
        self,
        creator_id: int,
        horizon_days: int = 90,
        platform: Optional[PlatformEnum] = None,
        income_type: Optional[IncomeTypeEnum] = None
    ) -> ForecastResponse:
        """
        Generate income forecast for a creator.

        Args:
            creator_id: Creator ID
            horizon_days: Number of days to forecast
            platform: Optional specific platform
            income_type: Optional specific income type

        Returns:
            ForecastResponse with predictions
        """
        # Get historical income data
        income_data = self._get_historical_income(
            creator_id=creator_id,
            platform=platform,
            income_type=income_type
        )

        if len(income_data) < 30:
            raise ValueError("Not enough historical data. Need at least 30 days.")

        # Prepare data for Prophet
        df = self._prepare_prophet_data(income_data)

        # Train Prophet model
        model = Prophet(
            daily_seasonality=False,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(df)

        # Generate forecast
        future = model.make_future_dataframe(periods=horizon_days, freq='D')
        forecast = model.predict(future)

        # Extract future predictions only
        forecast_future = forecast.tail(horizon_days)

        # Save forecast to database
        forecast_records = []
        for _, row in forecast_future.iterrows():
            forecast_record = ForecastData(
                creator_id=creator_id,
                forecast_date=row['ds'],
                predicted_income=max(row['yhat'], 0),  # Ensure non-negative
                confidence_lower=max(row['yhat_lower'], 0),
                confidence_upper=max(row['yhat_upper'], 0),
                model_version=settings.ATTRIBUTION_MODEL_VERSION,
                platform=platform,
                income_type=income_type,
                features_used={
                    "horizon_days": horizon_days,
                    "historical_days": len(income_data)
                }
            )
            self.db.add(forecast_record)
            forecast_records.append(forecast_record)

        self.db.commit()

        # Prepare response
        forecast_data_points = [
            ForecastDataPoint(
                date=record.forecast_date,
                predicted_income=record.predicted_income,
                confidence_lower=record.confidence_lower,
                confidence_upper=record.confidence_upper
            )
            for record in forecast_records
        ]

        total_predicted = sum(record.predicted_income for record in forecast_records)

        return ForecastResponse(
            creator_id=creator_id,
            forecast_data=forecast_data_points,
            total_predicted_income=total_predicted,
            model_version=settings.ATTRIBUTION_MODEL_VERSION,
            generated_at=datetime.utcnow(),
            accuracy_metrics=self._calculate_accuracy_metrics(model, df)
        )

    def _get_historical_income(
        self,
        creator_id: int,
        platform: Optional[PlatformEnum] = None,
        income_type: Optional[IncomeTypeEnum] = None,
        lookback_days: int = 365
    ) -> List[Income]:
        """
        Get historical income data for training.

        Args:
            creator_id: Creator ID
            platform: Optional platform filter
            income_type: Optional income type filter
            lookback_days: Days of history to retrieve

        Returns:
            List of Income records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=lookback_days)

        query = self.db.query(Income).filter(
            Income.creator_id == creator_id,
            Income.income_date >= cutoff_date,
            Income.is_verified == True
        )

        if platform:
            query = query.filter(Income.platform == platform)

        if income_type:
            query = query.filter(Income.income_type == income_type)

        return query.order_by(Income.income_date).all()

    def _prepare_prophet_data(self, income_data: List[Income]) -> pd.DataFrame:
        """
        Prepare data in Prophet format (ds, y columns).

        Args:
            income_data: List of Income records

        Returns:
            DataFrame with 'ds' and 'y' columns
        """
        # Aggregate income by date
        daily_income = {}
        for income in income_data:
            date_key = income.income_date.date()
            if date_key in daily_income:
                daily_income[date_key] += income.amount
            else:
                daily_income[date_key] = income.amount

        # Create DataFrame
        df = pd.DataFrame([
            {"ds": date, "y": amount}
            for date, amount in sorted(daily_income.items())
        ])

        # Fill missing dates with 0
        df['ds'] = pd.to_datetime(df['ds'])
        df = df.set_index('ds').asfreq('D', fill_value=0).reset_index()

        return df

    def _calculate_accuracy_metrics(
        self,
        model: Prophet,
        historical_df: pd.DataFrame
    ) -> dict:
        """
        Calculate model accuracy metrics using cross-validation.

        Args:
            model: Trained Prophet model
            historical_df: Historical data DataFrame

        Returns:
            Dictionary with accuracy metrics
        """
        from prophet.diagnostics import cross_validation, performance_metrics

        try:
            # Perform cross-validation
            df_cv = cross_validation(
                model,
                initial='180 days',
                period='30 days',
                horizon='30 days'
            )

            # Calculate performance metrics
            df_p = performance_metrics(df_cv)

            return {
                "mape": float(df_p['mape'].mean()),  # Mean Absolute Percentage Error
                "rmse": float(df_p['rmse'].mean()),  # Root Mean Squared Error
                "mae": float(df_p['mae'].mean()),    # Mean Absolute Error
            }
        except:
            # Not enough data for cross-validation
            return {
                "mape": None,
                "rmse": None,
                "mae": None
            }
