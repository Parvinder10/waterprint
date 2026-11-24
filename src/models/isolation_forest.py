"""Multivariate Isolation Forest Anomaly Detection Module for WATERPRINT.

Applies unsupervised tree-based space partitioning on joint flow,
residual, and pressure feature spaces to detect complex multivariate hydraulic anomalies.
"""

from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from src.utils.logging import logger
from src.utils.config import IsolationForestConfig

class WaterIsolationForest:
    """Unsupervised multivariate anomaly detector for water distribution systems."""
    
    def __init__(self, config: Optional[IsolationForestConfig] = None):
        self.cfg = config or IsolationForestConfig()
        self.model: Optional[IsolationForest] = None
        self.feature_cols: List[str] = []
        self.is_fitted: bool = False
        
    def _extract_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Identifies and prepares the multivariate feature matrix."""
        candidate_cols = [
            "flow_residual", "residual_zscore", "flow_delta_1",
            "pressure_mean", "pressure_drop_m", "is_mnf_window"
        ]
        available_cols = [c for c in candidate_cols if c in df.columns]
        if not available_cols:
            available_cols = ["flow_rate"]
            
        X = df[available_cols].copy().fillna(0.0)
        return X, available_cols

    def fit(self, train_df: pd.DataFrame):
        """Fits the Isolation Forest on uncompromised historical baseline features.
        
        Args:
            train_df: Historical training DataFrame.
        """
        logger.info(f"Fitting IsolationForest on {len(train_df)} samples...")
        X, cols = self._extract_features(train_df)
        self.feature_cols = cols
        
        self.model = IsolationForest(
            n_estimators=self.cfg.n_estimators,
            contamination=self.cfg.contamination,
            max_samples=self.cfg.max_samples,
            random_state=self.cfg.random_state,
            n_jobs=-1
        )
        self.model.fit(X)
        self.is_fitted = True
        logger.info("IsolationForest fitted successfully.")
        return self

    def predict(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Infers continuous anomaly scores and binary anomaly flags.
        
        Args:
            df: Feature DataFrame.
            
        Returns:
            Tuple of (anomaly_scores, binary_alarm_mask).
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("IsolationForest must be fitted before prediction.")
            
        X = df[self.feature_cols].copy().fillna(0.0)
        # raw decision function: negative values indicate outliers
        scores = self.model.decision_function(X)
        # binary predictions: -1 for outlier, 1 for inlier
        raw_preds = self.model.predict(X)
        alarm_mask = raw_preds == -1
        
        # Invert score so higher value = higher anomaly likelihood [0.0, 1.0]
        norm_scores = 1.0 / (1.0 + np.exp(scores * 5.0))
        return norm_scores, alarm_mask
