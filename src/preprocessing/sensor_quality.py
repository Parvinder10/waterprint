"""Sensor Health & Data Quality Assurance Module for WATERPRINT.

Performs multi-criteria sensor validation:
- Physical boundary compliance (flow >= 0, plausible pressure limits)
- ADC converter freeze / flatline detection
- Rate-of-change and jump filter
- Missing telemetry analysis and controlled interpolation

CRITICAL PRINCIPLE: Sensor anomalies are logged into a separate diagnostic registry
and strictly isolated from physical hydraulic leak evidence.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from src.utils.logging import logger
from src.utils.config import SensorQualityConfig

class SensorQualityChecker:
    """Evaluates telemetry data quality, flags hardware glitches, and cleans signals."""
    
    def __init__(self, config: Optional[SensorQualityConfig] = None):
        self.cfg = config or SensorQualityConfig()
        
    def evaluate_quality(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
        """Scans dataset for sensor anomalies, isolates hardware faults, and imputes clean series.
        
        Args:
            df: Aligned time-series DataFrame.
            
        Returns:
            Tuple of:
            - cleaned_df: DataFrame with imputed series and quality flag columns.
            - fault_log_df: Detailed registry of detected sensor hardware/telemetry faults.
            - quality_summary: Dictionary of quality metrics and completeness ratios.
        """
        logger.info("Executing sensor health and telemetry quality validation...")
        cleaned = df.copy()
        fault_records = []
        
        # 1. Identify pressure and flow columns
        flow_cols = [c for c in cleaned.columns if "flow_rate" in c]
        pressure_cols = [c for c in cleaned.columns if c.startswith("pressure_")]
        
        # Quality flag indicator columns
        cleaned["sensor_fault_active"] = False
        cleaned["telemetry_imputed"] = False
        
        # 2. Check Flow Telemetry
        for col in flow_cols:
            series = cleaned[col].copy()
            
            # Missing check
            null_mask = series.isna()
            if null_mask.any():
                for idx in cleaned.index[null_mask]:
                    fault_records.append({
                        "timestamp": cleaned.loc[idx, "timestamp"],
                        "sensor_id": col,
                        "sensor_type": "FLOW",
                        "fault_type": "MISSING_PACKET",
                        "severity": "WARNING",
                        "raw_value": np.nan,
                        "description": "Telemetry gap / packet drop detected"
                    })
                    
            # Out of bounds
            oob_mask = (series < self.cfg.flow_min_valid) | (series > self.cfg.flow_max_valid)
            for idx in cleaned.index[oob_mask]:
                val = series.loc[idx]
                fault_records.append({
                    "timestamp": cleaned.loc[idx, "timestamp"],
                    "sensor_id": col,
                    "sensor_type": "FLOW",
                    "fault_type": "OUT_OF_BOUNDS",
                    "severity": "CRITICAL",
                    "raw_value": val,
                    "description": f"Flow {val:.1f} m3/h violates physical limits [{self.cfg.flow_min_valid}, {self.cfg.flow_max_valid}]"
                })
                series.loc[idx] = np.nan
                
            # Flatline check (frozen sensor reading for >= max_flatline_consecutive steps)
            diffs = series.diff().abs()
            is_zero_diff = (diffs == 0.0)
            # Find runs of zeros
            run_lengths = is_zero_diff.astype(int).groupby((~is_zero_diff).cumsum()).cumsum()
            flatline_mask = run_lengths >= self.cfg.max_flatline_consecutive
            for idx in cleaned.index[flatline_mask]:
                val = series.loc[idx]
                fault_records.append({
                    "timestamp": cleaned.loc[idx, "timestamp"],
                    "sensor_id": col,
                    "sensor_type": "FLOW",
                    "fault_type": "FLATLINE",
                    "severity": "WARNING",
                    "raw_value": val,
                    "description": f"Sensor value frozen at {val:.2f} for >= {self.cfg.max_flatline_consecutive} consecutive intervals"
                })
                
            # Rate of change spike (instantaneous jump > limit)
            diff_from_prev = series.diff().abs()
            spike_mask = diff_from_prev > self.cfg.max_flow_rate_of_change
            for idx in cleaned.index[spike_mask]:
                jump = diff_from_prev.loc[idx]
                fault_records.append({
                    "timestamp": cleaned.loc[idx, "timestamp"],
                    "sensor_id": col,
                    "sensor_type": "FLOW",
                    "fault_type": "RATE_SPIKE",
                    "severity": "WARNING",
                    "raw_value": series.loc[idx],
                    "description": f"Flow rate surge of {jump:.1f} m3/h per step exceeds maximum plausible hydraulic change"
                })
                # Filter out the transient single-step spike for clean baseline
                series.loc[idx] = np.nan
                
            # Controlled linear interpolation for isolated gaps
            interpolated = series.interpolate(method="linear", limit=self.cfg.missing_interpolation_limit)
            imputed_mask = series.isna() & interpolated.notna()
            cleaned.loc[imputed_mask, "telemetry_imputed"] = True
            cleaned[col] = interpolated
            
        # 3. Check Pressure Telemetry
        for col in pressure_cols:
            series = cleaned[col].copy()
            
            # Missing check
            null_mask = series.isna()
            if null_mask.any():
                for idx in cleaned.index[null_mask]:
                    fault_records.append({
                        "timestamp": cleaned.loc[idx, "timestamp"],
                        "sensor_id": col,
                        "sensor_type": "PRESSURE",
                        "fault_type": "MISSING_PACKET",
                        "severity": "WARNING",
                        "raw_value": np.nan,
                        "description": "Pressure telemetry packet dropped"
                    })
                    
            # Out of bounds
            oob_mask = (series < self.cfg.pressure_min_valid) | (series > self.cfg.pressure_max_valid)
            for idx in cleaned.index[oob_mask]:
                val = series.loc[idx]
                fault_records.append({
                    "timestamp": cleaned.loc[idx, "timestamp"],
                    "sensor_id": col,
                    "sensor_type": "PRESSURE",
                    "fault_type": "OUT_OF_BOUNDS",
                    "severity": "CRITICAL",
                    "raw_value": val,
                    "description": f"Pressure head {val:.1f} m outside plausible range [{self.cfg.pressure_min_valid}, {self.cfg.pressure_max_valid}]"
                })
                series.loc[idx] = np.nan
                
            # Rate of change
            diff_from_prev = series.diff().abs()
            spike_mask = diff_from_prev > self.cfg.max_pressure_rate_of_change
            for idx in cleaned.index[spike_mask]:
                jump = diff_from_prev.loc[idx]
                fault_records.append({
                    "timestamp": cleaned.loc[idx, "timestamp"],
                    "sensor_id": col,
                    "sensor_type": "PRESSURE",
                    "fault_type": "RATE_SPIKE",
                    "severity": "WARNING",
                    "raw_value": series.loc[idx],
                    "description": f"Pressure shockwave of {jump:.1f} m head per step exceeds physical threshold"
                })
                series.loc[idx] = np.nan
                
            # Interpolation
            interpolated = series.interpolate(method="linear", limit=self.cfg.missing_interpolation_limit)
            imputed_mask = series.isna() & interpolated.notna()
            cleaned.loc[imputed_mask, "telemetry_imputed"] = True
            cleaned[col] = interpolated

        # Format fault log
        if fault_records:
            fault_log_df = pd.DataFrame(fault_records)
            # Mark timestamps in cleaned df where sensor faults occurred
            faulty_timestamps = set(fault_log_df["timestamp"])
            cleaned["sensor_fault_active"] = cleaned["timestamp"].isin(faulty_timestamps)
        else:
            fault_log_df = pd.DataFrame(columns=[
                "timestamp", "sensor_id", "sensor_type", "fault_type", "severity", "raw_value", "description"
            ])
            
        # Summary statistics
        total_cells = len(cleaned) * (len(flow_cols) + len(pressure_cols))
        total_faults = len(fault_records)
        cleanliness_score = max(0.0, 1.0 - (total_faults / max(1, total_cells))) * 100.0
        
        quality_summary = {
            "total_timesteps": len(cleaned),
            "flow_sensors_monitored": len(flow_cols),
            "pressure_sensors_monitored": len(pressure_cols),
            "total_sensor_fault_events": total_faults,
            "data_completeness_pct": float(np.round(cleanliness_score, 2)),
            "hardware_health_status": "EXCELLENT" if cleanliness_score > 98.0 else ("GOOD" if cleanliness_score > 95.0 else "DEGRADED")
        }
        
        logger.info(f"Sensor Quality Check Complete: {total_faults} faults logged. Health Status: {quality_summary['hardware_health_status']}")
        return cleaned, fault_log_df, quality_summary
