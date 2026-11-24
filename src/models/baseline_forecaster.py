"""Machine Learning Baseline Flow Forecaster for WATERPRINT.

Trains probabilistic baseline models (Quantile Gradient Boosting) on certified
uncompromised historical periods to estimate expected diurnal/seasonal water flow
along with 95% prediction intervals (Bayesian/empirical uncertainty bounds).
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from src.utils.logging import logger
from src.utils.config import BaselineForecasterConfig
from src.utils.exceptions import ModelFittingError

class BaselineFlowForecaster:
    """Predicts expected uncompromised flow demand and empirical prediction intervals."""
    
    def __init__(self, config: Optional[BaselineForecasterConfig] = None):
        self.cfg = config or BaselineForecasterConfig()
        self.median_model: Optional[Any] = None
        self.lower_model: Optional[Any] = None
        self.upper_model: Optional[Any] = None
        self.feature_names: List[str] = []
        self.residual_std_: float = 1.0
        self.is_fitted: bool = False
        
    def _get_feature_matrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """Selects and aligns predictive feature columns."""
        candidate_cols = [
            "hour", "day_of_week", "is_weekend", "day_of_year",
            "sin_hour", "cos_hour", "sin_dow", "cos_dow",
            "flow_lag_96", "flow_lag_672",
            "flow_rolling_mean_96"
        ]
        available_cols = [c for c in candidate_cols if c in df.columns]
        if not available_cols:
            raise ModelFittingError("No valid predictive features found in dataframe.")
            
        return df[available_cols].bfill().fillna(0.0)

    def fit(self, train_df: pd.DataFrame, target_col: str = "flow_rate"):
        """Fits the probabilistic quantile models on uncompromised historical training data.
        
        Args:
            train_df: DataFrame containing historical training records (leak-free period).
            target_col: Name of the target flow column.
        """
        logger.info(f"Training BaselineFlowForecaster ({self.cfg.algorithm}) on {len(train_df)} samples...")
        X = self._get_feature_matrix(train_df)
        y = train_df[target_col].values
        
        # Filter NaNs if any
        valid_mask = ~np.isnan(y)
        X_clean = X[valid_mask]
        y_clean = y[valid_mask]
        
        self.feature_names = list(X.columns)
        
        if self.cfg.algorithm == "gradient_boosting":
            # Point predictor / Median (alpha=0.50)
            self.median_model = GradientBoostingRegressor(
                loss="quantile",
                alpha=0.50,
                n_estimators=self.cfg.n_estimators,
                max_depth=self.cfg.max_depth,
                learning_rate=self.cfg.learning_rate,
                random_state=self.cfg.random_state
            )
            self.median_model.fit(X_clean, y_clean)
            
            # Lower 95% bound (alpha=0.025)
            self.lower_model = GradientBoostingRegressor(
                loss="quantile",
                alpha=0.025,
                n_estimators=max(40, self.cfg.n_estimators // 2),
                max_depth=self.cfg.max_depth - 1,
                learning_rate=self.cfg.learning_rate,
                random_state=self.cfg.random_state
            )
            self.lower_model.fit(X_clean, y_clean)
            
            # Upper 95% bound (alpha=0.975)
            self.upper_model = GradientBoostingRegressor(
                loss="quantile",
                alpha=0.975,
                n_estimators=max(40, self.cfg.n_estimators // 2),
                max_depth=self.cfg.max_depth - 1,
                learning_rate=self.cfg.learning_rate,
                random_state=self.cfg.random_state
            )
            self.upper_model.fit(X_clean, y_clean)
            
            preds_train = self.median_model.predict(X_clean)
            residuals_train = y_clean - preds_train
            self.residual_std_ = float(np.std(residuals_train))
            
        else: # Regularized Ridge fallback
            ridge = Ridge(alpha=10.0)
            ridge.fit(X_clean, y_clean)
            self.median_model = ridge
            preds_train = ridge.predict(X_clean)
            residuals_train = y_clean - preds_train
            self.residual_std_ = float(np.std(residuals_train))
            
        self.is_fitted = True
        logger.info(f"Baseline Forecaster trained successfully. Baseline residual std: {self.residual_std_:.3f} m3/h.")
        return self

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generates expected baseline flow and lower/upper 95% prediction intervals.
        
        Args:
            df: Feature DataFrame.
            
        Returns:
            Tuple of (expected_median, lower_95_bound, upper_95_bound).
        """
        if not self.is_fitted:
            raise ModelFittingError("Model must be fitted before predict.")
            
        X = self._get_feature_matrix(df)
        
        if self.cfg.algorithm == "gradient_boosting" and self.upper_model is not None:
            expected = self.median_model.predict(X)
            lower = self.lower_model.predict(X)
            upper = self.upper_model.predict(X)
            # Ensure proper ordering: lower <= expected <= upper
            lower = np.minimum(lower, expected)
            upper = np.maximum(upper, expected)
        else:
            expected = self.median_model.predict(X)
            z_crit = 1.96 # 95% normal bound
            lower = expected - z_crit * self.residual_std_
            upper = expected + z_crit * self.residual_std_
            
        return expected, lower, upper
