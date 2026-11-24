"""Residual-Based Anomaly Detection Module for WATERPRINT.

Analyzes flow residuals (observed vs. expected) and cross-correlates
flow surpluses with concurrent hydraulic network pressure drops.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from src.utils.logging import logger

class ResidualAnomalyDetector:
    """Detects leaks by thresholding baseline residuals and cross-validating pressure drops."""
    
    def __init__(self, z_threshold: float = 2.50, pressure_drop_threshold_m: float = 0.40):
        self.z_threshold = z_threshold
        self.pressure_drop_threshold_m = pressure_drop_threshold_m
        
    def analyze_residuals(
        self,
        df: pd.DataFrame,
        observed_col: str = "flow_rate",
        expected_col: str = "expected_flow",
        upper_bound_col: str = "expected_upper_95",
        pressure_col: Optional[str] = "pressure_mean"
    ) -> pd.DataFrame:
        """Computes residuals, prediction interval breaches, and pressure drop corroboration.
        
        Args:
            df: DataFrame containing observed and forecasted series.
            observed_col: Column name for observed flow.
            expected_col: Column name for expected baseline flow.
            upper_bound_col: Column name for 95% upper bound.
            pressure_col: Column name for network mean pressure.
            
        Returns:
            DataFrame with residual metrics and binary anomaly flags.
        """
        logger.info("Computing residual-based flow anomalies and pressure cross-correlations...")
        res_df = df.copy()
        
        # 1. Flow Residual
        obs = res_df[observed_col].values
        exp = res_df[expected_col].values
        upper = res_df[upper_bound_col].values
        
        raw_residual = obs - exp
        res_df["flow_residual"] = np.round(raw_residual, 2)
        
        # Standardized residual
        res_std = np.nanstd(raw_residual)
        res_df["residual_zscore"] = np.round(raw_residual / max(1e-3, res_std), 2)
        
        # Prediction interval breach
        res_df["interval_breach"] = obs > upper
        
        # 2. Pressure Drop Corroboration
        if pressure_col in res_df.columns:
            # Baseline expected pressure accounts for diurnal cycle (hour & minute)
            ts = res_df["timestamp"]
            p_obs = res_df[pressure_col]
            # Diurnal baseline: median pressure for that specific 15-minute time-of-day interval
            diurnal_p_exp = res_df.groupby([ts.dt.hour, ts.dt.minute])[pressure_col].transform("median")
            # Excess pressure drop beyond normal diurnal head loss
            p_drop = diurnal_p_exp - p_obs
            
            res_df["pressure_drop_m"] = np.round(p_drop, 2)
            res_df["pressure_drop_flag"] = p_drop > self.pressure_drop_threshold_m
        else:
            res_df["pressure_drop_m"] = 0.0
            res_df["pressure_drop_flag"] = False
            
        # 3. High-Confidence Residual Anomaly
        # Triggers when flow residual breaches upper bound AND z-score exceeds threshold
        res_df["residual_anomaly_flag"] = (
            (res_df["interval_breach"]) | (res_df["residual_zscore"] > self.z_threshold)
        )
        
        return res_df
