"""Ensemble Anomaly Arbiter for WATERPRINT.

Fuses multiple analytical methods (baseline residuals, CUSUM change-points,
rolling Z-scores, Isolation Forest, and pressure corroboration) while strictly
filtering out sensor hardware/telemetry faults.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
from src.utils.logging import logger

class EnsembleAnomalyArbiter:
    """Ensemble detector aggregating multiple model predictions into validated leak events."""
    
    def __init__(self, persistence_steps: int = 3):
        self.persistence_steps = persistence_steps
        
    def evaluate_ensemble(
        self,
        df: pd.DataFrame,
        cusum_alarms: np.ndarray,
        iso_alarms: np.ndarray,
        iso_scores: np.ndarray
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Fuses model outputs and aggregates continuous time steps into discrete leak events.
        
        Args:
            df: DataFrame containing flow_residual, residual_zscore, pressure_drop_flag, sensor_fault_active.
            cusum_alarms: Boolean array of CUSUM change-point alarms.
            iso_alarms: Boolean array of Isolation Forest alarms.
            iso_scores: Continuous anomaly scores from Isolation Forest.
            
        Returns:
            Tuple of:
            - scored_df: Time-series DataFrame with combined anomaly scores and flags.
            - events_df: Discrete aggregated anomaly events table.
        """
        logger.info("Evaluating ensemble anomaly fusion and event aggregation...")
        scored = df.copy()
        n = len(scored)
        
        scored["cusum_alarm"] = cusum_alarms
        scored["iso_alarm"] = iso_alarms
        scored["iso_score"] = np.round(iso_scores, 3)
        
        # 1. Base individual indicators
        res_breach = scored["interval_breach"].values if "interval_breach" in scored.columns else (scored["residual_zscore"] > 2.5).values
        p_drop = scored["pressure_drop_flag"].values if "pressure_drop_flag" in scored.columns else np.zeros(n, dtype=bool)
        sensor_fault = scored["sensor_fault_active"].values if "sensor_fault_active" in scored.columns else np.zeros(n, dtype=bool)
        
        # 2. Voting / Composite Confidence Score (0.0 to 1.0)
        composite_score = (
            0.35 * res_breach.astype(float) +
            0.30 * cusum_alarms.astype(float) +
            0.20 * iso_scores +
            0.15 * p_drop.astype(float)
        )
        scored["ensemble_score"] = np.round(composite_score, 3)
        
        # 3. Raw Leak Candidate Alarm
        # A true leak exhibits positive volumetric loss (flow_residual > 4.0 m3/h)
        # coupled with persistent CUSUM drift or upper prediction interval breach
        flow_res = scored["flow_residual"].values if "flow_residual" in scored.columns else np.zeros(n)
        significant_loss = flow_res > 4.0
        
        raw_leak_alarm = significant_loss & (
            (composite_score >= 0.52) |
            (cusum_alarms & res_breach)
        )
        
        # CRITICAL SEPARATION PRINCIPLE: If a sensor hardware fault is active, suppress physical leak alarm!
        raw_leak_alarm = raw_leak_alarm & (~sensor_fault)
        
        # 4. Multi-step Temporal Persistence Filter & Gap Coalescing
        # Fill short momentary dips (<= 12 steps = 3 hrs) during diurnal inflection points
        series_alarm = pd.Series(raw_leak_alarm.astype(int))
        filled_alarm = series_alarm.rolling(window=13, min_periods=1, center=True).max().astype(bool)
        
        # Enforce persistence of at least 4 steps (1 hour)
        alarm_ints = filled_alarm.astype(int)
        groups = (alarm_ints != alarm_ints.shift()).cumsum()
        consecutive_counts = alarm_ints.groupby(groups).cumsum()
        
        confirmed_alarm = filled_alarm & (consecutive_counts >= 4)
        scored["leak_alarm_active"] = confirmed_alarm
        
        # 5. Aggregate Continuous Alarm Sequences into Discrete Events
        events = []
        in_event = False
        event_start_idx = 0
        event_id_counter = 1
        
        for i in range(n):
            if confirmed_alarm[i] and not in_event:
                in_event = True
                event_start_idx = i
            elif not confirmed_alarm[i] and in_event:
                in_event = False
                event_end_idx = i - 1
                
                # Create event record
                event_slice = scored.iloc[event_start_idx:event_end_idx + 1]
                duration_hours = len(event_slice) * 0.25
                peak_residual = float(event_slice["flow_residual"].max()) if "flow_residual" in event_slice.columns else 0.0
                mean_p_drop = float(event_slice["pressure_drop_m"].mean()) if "pressure_drop_m" in event_slice.columns else 0.0
                max_score = float(event_slice["ensemble_score"].max())
                
                # Determine Severity
                if peak_residual > 13.0 or (peak_residual > 9.0 and mean_p_drop > 0.60):
                    severity = "CRITICAL"
                elif peak_residual > 7.0 or mean_p_drop > 0.40:
                    severity = "HIGH"
                elif peak_residual > 4.0:
                    severity = "MEDIUM"
                else:
                    severity = "LOW"
                    
                t_start = str(event_slice["timestamp"].iloc[0])
                t_end = str(event_slice["timestamp"].iloc[-1])
                
                evidence = (
                    f"Flow residual peaked at {peak_residual:.1f} m3/h "
                    f"with concurrent network pressure depression of {mean_p_drop:.2f} m head. "
                    f"Confirmed across {len(event_slice)} consecutive 15-min periods."
                )
                
                events.append({
                    "event_id": f"EVT_{event_id_counter:03d}",
                    "dma_id": event_slice["dma_id"].iloc[0] if "dma_id" in event_slice.columns else "DMA_NORTH",
                    "start_time": t_start,
                    "end_time": t_end,
                    "duration_hours": round(duration_hours, 1),
                    "severity": severity,
                    "peak_flow_residual_m3h": round(peak_residual, 2),
                    "mean_pressure_drop_m": round(mean_p_drop, 2),
                    "confidence_score": round(max_score, 2),
                    "supporting_evidence": evidence
                })
                event_id_counter += 1
                
        # Handle trailing open event if dataset ends while alarm is active
        if in_event:
            event_slice = scored.iloc[event_start_idx:n]
            duration_hours = len(event_slice) * 0.25
            peak_residual = float(event_slice["flow_residual"].max())
            mean_p_drop = float(event_slice["pressure_drop_m"].mean())
            max_score = float(event_slice["ensemble_score"].max())
            events.append({
                "event_id": f"EVT_{event_id_counter:03d}",
                "dma_id": event_slice["dma_id"].iloc[0] if "dma_id" in event_slice.columns else "DMA_NORTH",
                "start_time": str(event_slice["timestamp"].iloc[0]),
                "end_time": str(event_slice["timestamp"].iloc[-1]),
                "duration_hours": round(duration_hours, 1),
                "severity": "HIGH" if peak_residual > 7.0 else "MEDIUM",
                "peak_flow_residual_m3h": round(peak_residual, 2),
                "mean_pressure_drop_m": round(mean_p_drop, 2),
                "confidence_score": round(max_score, 2),
                "supporting_evidence": f"Ongoing active anomaly: flow residual peaked at {peak_residual:.1f} m3/h."
            })
            
        # Coalesce events that are within 14 hours of each other into a single physical incident
        if len(events) > 1:
            coalesced = []
            curr = events[0]
            for nxt in events[1:]:
                curr_end = pd.to_datetime(curr["end_time"])
                nxt_start = pd.to_datetime(nxt["start_time"])
                gap_hrs = (nxt_start - curr_end).total_seconds() / 3600.0
                if gap_hrs <= 14.0:
                    # Merge nxt into curr
                    curr["end_time"] = nxt["end_time"]
                    curr["duration_hours"] = round(curr["duration_hours"] + nxt["duration_hours"] + gap_hrs, 1)
                    curr["peak_flow_residual_m3h"] = max(curr["peak_flow_residual_m3h"], nxt["peak_flow_residual_m3h"])
                    curr["mean_pressure_drop_m"] = round((curr["mean_pressure_drop_m"] + nxt["mean_pressure_drop_m"]) / 2.0, 2)
                    curr["confidence_score"] = max(curr["confidence_score"], nxt["confidence_score"])
                    if nxt["severity"] == "CRITICAL" or curr["severity"] == "CRITICAL":
                        curr["severity"] = "CRITICAL"
                    elif nxt["severity"] == "HIGH" or curr["severity"] == "HIGH":
                        curr["severity"] = "HIGH"
                else:
                    coalesced.append(curr)
                    curr = nxt
            coalesced.append(curr)
            
            # Re-index event IDs
            for i, evt in enumerate(coalesced, 1):
                evt["event_id"] = f"EVT_{i:03d}"
            events = coalesced

        events_df = pd.DataFrame(events) if events else pd.DataFrame(columns=[
            "event_id", "dma_id", "start_time", "end_time", "duration_hours", "severity",
            "peak_flow_residual_m3h", "mean_pressure_drop_m", "confidence_score", "supporting_evidence"
        ])
        
        logger.info(f"Ensemble detection completed: {len(events_df)} discrete leak events identified.")
        return scored, events_df
