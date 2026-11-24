"""Time-series alignment and temporal integrity module for WATERPRINT."""

from typing import Dict, Tuple, Optional
import pandas as pd
import numpy as np
from src.utils.logging import logger
from src.utils.exceptions import DataAlignmentError

class TimeSeriesAligner:
    """Synchronizes multi-rate telemetry streams onto a regular chronological grid."""
    
    def __init__(self, target_freq: str = "15min"):
        self.target_freq = target_freq
        
    def check_temporal_integrity(self, df: pd.DataFrame, time_col: str = "timestamp") -> Dict[str, any]:
        """Analyzes duplicate timestamps, missing intervals, and temporal continuity."""
        if time_col not in df.columns:
            raise DataAlignmentError(f"Column '{time_col}' not found in dataframe.")
            
        n_rows = len(df)
        n_unique_times = df[time_col].nunique()
        n_duplicates = n_rows - n_unique_times
        
        # Check regular spacing
        s_times = df[time_col].drop_duplicates().sort_values()
        diffs = s_times.diff().dropna()
        median_delta = diffs.median()
        
        # Expected complete range
        full_range = pd.date_range(start=s_times.min(), end=s_times.max(), freq=self.target_freq)
        n_expected = len(full_range)
        n_missing_intervals = n_expected - n_unique_times
        
        report = {
            "total_records": n_rows,
            "unique_timestamps": n_unique_times,
            "duplicate_timestamps": n_duplicates,
            "start_time": str(s_times.min()),
            "end_time": str(s_times.max()),
            "median_interval": str(median_delta),
            "expected_intervals": n_expected,
            "missing_time_steps": max(0, n_missing_intervals)
        }
        return report

    def align_and_merge(
        self,
        df_flow: pd.DataFrame,
        df_pressure: pd.DataFrame,
        df_consumption: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Aligns flow, pressure, and consumption dataframes onto a uniform chronological grid.
        
        Args:
            df_flow: DataFrame containing flow records.
            df_pressure: DataFrame containing pressure records.
            df_consumption: Optional DataFrame with smart meter consumption records.
            
        Returns:
            Unified synchronized DataFrame indexed by timestamp.
        """
        logger.info("Aligning multi-source time-series records...")
        
        # 1. Deduplicate if necessary
        df_f = df_flow.drop_duplicates(subset=["timestamp"]).copy()
        df_p = df_pressure.drop_duplicates(subset=["timestamp"]).copy()
        
        # 2. Merge on timestamp
        merged = pd.merge(df_f, df_p, on="timestamp", how="outer")
        
        if df_consumption is not None and not df_consumption.empty:
            df_c = df_consumption.drop_duplicates(subset=["timestamp"]).copy()
            # Drop redundant dma_id column if present before merge
            if "dma_id" in df_c.columns and "dma_id" in merged.columns:
                df_c = df_c.drop(columns=["dma_id"])
            merged = pd.merge(merged, df_c, on="timestamp", how="outer")
            
        # 3. Sort chronologically
        merged = merged.sort_values("timestamp").reset_index(drop=True)
        
        # 4. Enforce complete uniform grid
        min_time = merged["timestamp"].min()
        max_time = merged["timestamp"].max()
        complete_grid = pd.date_range(start=min_time, end=max_time, freq=self.target_freq, name="timestamp")
        
        aligned_df = pd.DataFrame({"timestamp": complete_grid})
        aligned_df = pd.merge(aligned_df, merged, on="timestamp", how="left")
        
        logger.info(f"Synchronized grid spans {min_time} to {max_time} ({len(aligned_df)} steps).")
        return aligned_df
