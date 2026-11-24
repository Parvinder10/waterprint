"""Feature Engineering Pipeline for WATERPRINT.

Extracts hydraulic, temporal, autoregressive lag, and Minimum Night Flow (MNF)
features required for baseline forecasting, residual analysis, and anomaly detection.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from src.utils.logging import logger
from src.utils.config import FeaturesConfig

class FeatureEngineer:
    """Transforms raw cleaned sensor time-series into rich hydraulic and temporal feature spaces."""
    
    def __init__(self, config: Optional[FeaturesConfig] = None):
        self.cfg = config or FeaturesConfig()
        
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Computes all engineered features on the input dataframe.
        
        Args:
            df: Cleaned time-series DataFrame with timestamp, flow, and pressure.
            
        Returns:
            DataFrame augmented with engineered features.
        """
        logger.info("Computing temporal, hydraulic, and lag features...")
        feat_df = df.copy()
        
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(feat_df["timestamp"]):
            feat_df["timestamp"] = pd.to_datetime(feat_df["timestamp"])
            
        ts = feat_df["timestamp"]
        
        # 1. Temporal & Calendar Encodings
        hour_fraction = ts.dt.hour + ts.dt.minute / 60.0
        dow = ts.dt.dayofweek
        
        feat_df["hour"] = ts.dt.hour
        feat_df["day_of_week"] = dow
        feat_df["is_weekend"] = (dow >= 5).astype(int)
        feat_df["day_of_year"] = ts.dt.dayofyear
        
        # Sinusoidal periodic encodings (continuous circle representation)
        feat_df["sin_hour"] = np.sin(2.0 * np.pi * hour_fraction / 24.0)
        feat_df["cos_hour"] = np.cos(2.0 * np.pi * hour_fraction / 24.0)
        feat_df["sin_dow"] = np.sin(2.0 * np.pi * dow / 7.0)
        feat_df["cos_dow"] = np.cos(2.0 * np.pi * dow / 7.0)
        
        # 2. Minimum Night Flow (MNF) Window Indicator (02:00 to 04:00 AM)
        feat_df["is_mnf_window"] = (ts.dt.hour >= self.cfg.mnf_start_hour) & (ts.dt.hour < self.cfg.mnf_end_hour)
        
        # 3. Flow Lags & Rolling Window Statistics
        if "flow_rate" in feat_df.columns:
            s_flow = feat_df["flow_rate"]
            
            # Autoregressive lags
            if self.cfg.include_lag_features:
                for lag in self.cfg.lag_steps:
                    feat_df[f"flow_lag_{lag}"] = s_flow.shift(lag)
                    
            # Rolling statistics (1h = 4 steps, 3h = 12 steps, 24h = 96 steps)
            for w in self.cfg.rolling_windows:
                feat_df[f"flow_rolling_mean_{w}"] = s_flow.rolling(window=w, min_periods=1).mean()
                feat_df[f"flow_rolling_std_{w}"] = s_flow.rolling(window=w, min_periods=1).std().fillna(0.0)
                
            # Instantaneous rate-of-change (derivative)
            feat_df["flow_delta_1"] = s_flow.diff().fillna(0.0)
            
        # 4. Pressure Spatial & Temporal Features
        p_cols = [c for c in feat_df.columns if c.startswith("pressure_")]
        if p_cols:
            feat_df["pressure_mean"] = feat_df[p_cols].mean(axis=1)
            feat_df["pressure_min"] = feat_df[p_cols].min(axis=1)
            feat_df["pressure_std"] = feat_df[p_cols].std(axis=1).fillna(0.0)
            
            # Spatial deviation for each sensor from network mean
            for p_col in p_cols:
                feat_df[f"{p_col}_dev_from_mean"] = feat_df[p_col] - feat_df["pressure_mean"]
                
            # Rolling mean network pressure (1h = 4 steps)
            feat_df["pressure_mean_rolling_4"] = feat_df["pressure_mean"].rolling(window=4, min_periods=1).mean()
            feat_df["pressure_delta_1"] = feat_df["pressure_mean"].diff().fillna(0.0)

        # 5. Consumption & Water Balance Features
        cons_cols = [c for c in ["metered_consumption", "commercial_consumption"] if c in feat_df.columns]
        if cons_cols and "flow_rate" in feat_df.columns:
            feat_df["total_authorized_consumption"] = feat_df[cons_cols].sum(axis=1)
            feat_df["unexplained_water_diff"] = feat_df["flow_rate"] - feat_df["total_authorized_consumption"]
        elif "flow_rate" in feat_df.columns:
            # Fallback if consumption not available
            feat_df["total_authorized_consumption"] = np.nan
            feat_df["unexplained_water_diff"] = np.nan
            
        logger.info(f"Feature engineering completed: generated {len(feat_df.columns)} total columns.")
        return feat_df
