"""Benchmark Comparison Engine for WATERPRINT.

Compares WATERPRINT's multi-tier analytical ensemble against industry standard
baselines (Fixed Static Threshold, Rolling Mean + 3-Sigma, and Unsupervised Isolation Forest).
"""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from src.evaluation.metrics import WaterLossEvaluator
from src.utils.logging import logger

class BenchmarkComparator:
    """Evaluates and compares baseline methods against WATERPRINT."""
    
    def __init__(self, evaluator: Optional[WaterLossEvaluator] = None):
        self.evaluator = evaluator or WaterLossEvaluator()
        
    def _run_static_baseline(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> pd.DataFrame:
        """Baseline 1: Fixed Static Upper Bound (95th percentile of historical inflow)."""
        static_threshold = train_df["flow_rate"].quantile(0.95)
        raw_alarms = (test_df["flow_rate"] > static_threshold).astype(int)
        
        # Simple persistence (>= 3 periods)
        groups = (raw_alarms != raw_alarms.shift()).cumsum()
        counts = raw_alarms.groupby(groups).cumsum()
        confirmed = (raw_alarms == 1) & (counts >= 3)
        
        return self._extract_events(test_df, confirmed, "BL_STATIC")

    def _run_rolling_baseline(self, test_df: pd.DataFrame) -> pd.DataFrame:
        """Baseline 2: Rolling 24h Mean + 2.5 Sigma Threshold."""
        s = test_df["flow_rate"]
        rolling_mean = s.rolling(window=96, min_periods=24).mean()
        rolling_std = s.rolling(window=96, min_periods=24).std().fillna(1.0)
        
        threshold = rolling_mean + 2.5 * rolling_std
        raw_alarms = (s > threshold).astype(int)
        
        groups = (raw_alarms != raw_alarms.shift()).cumsum()
        counts = raw_alarms.groupby(groups).cumsum()
        confirmed = (raw_alarms == 1) & (counts >= 3)
        
        return self._extract_events(test_df, confirmed, "BL_ROLLING")

    def _run_iso_baseline(self, train_df: pd.DataFrame, test_df: pd.DataFrame) -> pd.DataFrame:
        """Baseline 3: Standalone Isolation Forest (Flow only)."""
        iso = IsolationForest(contamination=0.035, random_state=42)
        X_train = train_df[["flow_rate"]].fillna(0.0)
        iso.fit(X_train)
        
        X_test = test_df[["flow_rate"]].fillna(0.0)
        preds = iso.predict(X_test)
        raw_alarms = pd.Series((preds == -1).astype(int), index=test_df.index)
        
        groups = (raw_alarms != raw_alarms.shift()).cumsum()
        counts = raw_alarms.groupby(groups).cumsum()
        confirmed = (raw_alarms == 1) & (counts >= 3)
        
        return self._extract_events(test_df, confirmed, "BL_ISOFOREST")

    def _extract_events(self, df: pd.DataFrame, mask: pd.Series, prefix: str) -> pd.DataFrame:
        """Extracts start and end times for contiguous alarm periods."""
        events = []
        in_evt = False
        start_idx = 0
        evt_cnt = 1
        
        times = df["timestamp"].values
        m_vals = mask.values
        
        for i in range(len(m_vals)):
            if m_vals[i] and not in_evt:
                in_evt = True
                start_idx = i
            elif not m_vals[i] and in_evt:
                in_evt = False
                events.append({
                    "event_id": f"{prefix}_{evt_cnt:03d}",
                    "start_time": pd.to_datetime(times[start_idx]),
                    "end_time": pd.to_datetime(times[i - 1]),
                    "duration_hours": (i - start_idx) * 0.25
                })
                evt_cnt += 1
                
        if in_evt:
            events.append({
                "event_id": f"{prefix}_{evt_cnt:03d}",
                "start_time": pd.to_datetime(times[start_idx]),
                "end_time": pd.to_datetime(times[-1]),
                "duration_hours": (len(m_vals) - start_idx) * 0.25
            })
            
        # Coalesce events within 8 hours
        if len(events) > 1:
            coalesced = []
            curr = events[0]
            for nxt in events[1:]:
                curr_end = pd.to_datetime(curr["end_time"])
                nxt_start = pd.to_datetime(nxt["start_time"])
                gap_hrs = (nxt_start - curr_end).total_seconds() / 3600.0
                if gap_hrs <= 8.0:
                    curr["end_time"] = nxt["end_time"]
                    curr["duration_hours"] = round(curr["duration_hours"] + nxt["duration_hours"] + gap_hrs, 1)
                else:
                    coalesced.append(curr)
                    curr = nxt
            coalesced.append(curr)
            for i, evt in enumerate(coalesced, 1):
                evt["event_id"] = f"{prefix}_{i:03d}"
            events = coalesced

        return pd.DataFrame(events) if events else pd.DataFrame(columns=["event_id", "start_time", "end_time", "duration_hours"])

    def run_benchmark_comparison(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        waterprint_events: pd.DataFrame,
        ground_truth_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Runs all baselines and compiles comparative performance matrix.
        
        Returns:
            DataFrame comparing metrics across all models.
        """
        logger.info("Running comparative benchmark against simple baselines...")
        t_start = test_df["timestamp"].min()
        t_end = test_df["timestamp"].max()
        
        # 1. Run Baselines
        bl_static_events = self._run_static_baseline(train_df, test_df)
        bl_rolling_events = self._run_rolling_baseline(test_df)
        bl_iso_events = self._run_iso_baseline(train_df, test_df)
        
        # 2. Evaluate Each
        m_static = self.evaluator.evaluate_detections(bl_static_events, ground_truth_df, t_start, t_end)
        m_rolling = self.evaluator.evaluate_detections(bl_rolling_events, ground_truth_df, t_start, t_end)
        m_iso = self.evaluator.evaluate_detections(bl_iso_events, ground_truth_df, t_start, t_end)
        m_waterprint = self.evaluator.evaluate_detections(waterprint_events, ground_truth_df, t_start, t_end)
        
        records = [
            {
                "Method": "Fixed Static Threshold",
                "Precision": m_static["precision"],
                "Recall": m_static["recall"],
                "F1_Score": m_static["f1_score"],
                "Mean_Delay_Hours": m_static["mean_detection_delay_hours"],
                "False_Alarms_Per_Month": m_static["false_alarms_per_month"],
                "Localisation_Support": "None"
            },
            {
                "Method": "Rolling Mean + 2.5σ",
                "Precision": m_rolling["precision"],
                "Recall": m_rolling["recall"],
                "F1_Score": m_rolling["f1_score"],
                "Mean_Delay_Hours": m_rolling["mean_detection_delay_hours"],
                "False_Alarms_Per_Month": m_rolling["false_alarms_per_month"],
                "Localisation_Support": "None"
            },
            {
                "Method": "Standalone Isolation Forest",
                "Precision": m_iso["precision"],
                "Recall": m_iso["recall"],
                "F1_Score": m_iso["f1_score"],
                "Mean_Delay_Hours": m_iso["mean_detection_delay_hours"],
                "False_Alarms_Per_Month": m_iso["false_alarms_per_month"],
                "Localisation_Support": "None"
            },
            {
                "Method": "WATERPRINT Multi-Tier Ensemble",
                "Precision": m_waterprint["precision"],
                "Recall": m_waterprint["recall"],
                "F1_Score": m_waterprint["f1_score"],
                "Mean_Delay_Hours": m_waterprint["mean_detection_delay_hours"],
                "False_Alarms_Per_Month": m_waterprint["false_alarms_per_month"],
                "Localisation_Support": "Hydraulic Pressure Matrix & Graph Ranking"
            }
        ]
        
        comparison_df = pd.DataFrame(records)
        return comparison_df
