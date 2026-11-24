"""Statistical Anomaly & Sequential Change-Point Detection Module for WATERPRINT.

Implements:
- Rolling Z-score anomaly scoring with robust IQR options
- Tabular Cumulative Sum (CUSUM) sequential change-point detection
- Multi-step temporal persistence filter to eliminate transient false alarms
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from src.utils.logging import logger
from src.utils.config import StatisticalDetectorConfig

class StatisticalDetector:
    """Applies sequential statistical hypothesis testing and CUSUM change-point filters."""
    
    def __init__(self, config: Optional[StatisticalDetectorConfig] = None):
        self.cfg = config or StatisticalDetectorConfig()
        
    def detect_rolling_zscore(
        self,
        series: pd.Series,
        window: Optional[int] = None,
        threshold: Optional[float] = None
    ) -> Tuple[pd.Series, pd.Series]:
        """Calculates rolling Z-scores and flags points exceeding threshold.
        
        Args:
            series: Univariate continuous series (e.g. flow_rate or residual).
            window: Rolling window size (default from config, e.g. 96 steps = 24h).
            threshold: Z-score decision threshold (default from config, e.g. 2.75).
            
        Returns:
            Tuple of (z_scores, binary_alarm_mask).
        """
        w = window or self.cfg.rolling_window
        thresh = threshold or self.cfg.z_score_threshold
        
        rolling_mean = series.rolling(window=w, min_periods=w // 2).mean()
        rolling_std = series.rolling(window=w, min_periods=w // 2).std().replace(0.0, np.nan)
        
        z_scores = (series - rolling_mean) / rolling_std
        z_scores = z_scores.fillna(0.0)
        
        alarm_mask = z_scores > thresh
        return z_scores, alarm_mask

    def detect_cusum_changepoint(
        self,
        residuals: pd.Series,
        drift: Optional[float] = None,
        threshold: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Runs tabular one-sided CUSUM algorithm to detect sustained positive drift.
        
        Args:
            residuals: Standardized residual series or flow deviation.
            drift: Slack / allowance parameter k (in standard deviations).
            threshold: Decision limit h (in standard deviations).
            
        Returns:
            Tuple of (cusum_statistics, binary_changepoint_alarm_mask).
        """
        k = drift if drift is not None else self.cfg.cusum_drift
        h = threshold if threshold is not None else self.cfg.cusum_threshold
        
        vals = residuals.fillna(0.0).values
        n = len(vals)
        s_pos = np.zeros(n)
        alarms = np.zeros(n, dtype=bool)
        
        for t in range(1, n):
            s_pos[t] = max(0.0, s_pos[t - 1] + vals[t] - k)
            if s_pos[t] > h:
                alarms[t] = True
                
        return s_pos, alarms

    def apply_persistence_filter(self, raw_alarms: pd.Series, min_consecutive: Optional[int] = None) -> pd.Series:
        """Suppresses transient isolated alarms; triggers only after min_consecutive positive steps.
        
        Args:
            raw_alarms: Boolean Series of preliminary alarms.
            min_consecutive: Number of consecutive alarm steps required (default from config).
            
        Returns:
            Filtered boolean Series with transient spikes removed.
        """
        m = min_consecutive or self.cfg.persistence_steps
        # Run length encoding
        alarm_ints = raw_alarms.astype(int)
        # Groups consecutive identical values
        groups = (alarm_ints != alarm_ints.shift()).cumsum()
        consecutive_counts = alarm_ints.groupby(groups).cumsum()
        
        # Keep only points where run length >= m
        filtered = (raw_alarms) & (consecutive_counts >= m)
        return filtered
