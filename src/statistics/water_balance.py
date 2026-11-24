"""Water Balance & Nocturnal Minimum Night Flow (MNF) Analysis Module for WATERPRINT.

Implements standard International Water Association (IWA) water audit accounting,
diurnal Minimum Night Flow (MNF) extraction, Net Night Flow (NNF) calculation,
and Infrastructure Leakage Index (ILI) estimation.
"""

from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from src.utils.logging import logger

class WaterBalanceAnalyzer:
    """Performs macroscopic water audit and nocturnal minimum night flow analysis."""
    
    def __init__(
        self,
        mnf_start_hour: int = 2,
        mnf_end_hour: int = 4,
        properties_count: int = 2450,
        mains_length_km: float = 28.5,
        avg_pressure_m: float = 48.0,
        legitimate_night_use_per_prop_lph: float = 1.8
    ):
        self.mnf_start_hour = mnf_start_hour
        self.mnf_end_hour = mnf_end_hour
        self.properties_count = properties_count
        self.mains_length_km = mains_length_km
        self.avg_pressure_m = avg_pressure_m
        self.legitimate_night_use_per_prop_lph = legitimate_night_use_per_prop_lph
        
    def compute_macro_water_balance(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates the standard IWA water balance for the given time horizon.
        
        Args:
            df: DataFrame containing flow_rate and total_authorized_consumption.
            
        Returns:
            Dictionary with volumetric audit breakdowns and NRW indicators.
        """
        logger.info("Computing macro IWA water balance...")
        
        # Volumetric integration: 15-min interval = 0.25 hour
        time_step_hours = 0.25
        total_siv_m3 = float((df["flow_rate"] * time_step_hours).sum())
        
        if "total_authorized_consumption" in df.columns and df["total_authorized_consumption"].notna().any():
            billed_authorized_m3 = float((df["total_authorized_consumption"] * time_step_hours).sum())
        else:
            # Estimate 78% authorized if metered consumption column missing
            billed_authorized_m3 = 0.78 * total_siv_m3
            
        # Unbilled authorized (mains flushing, firefighting, public fountains ~ 2.5% of SIV)
        unbilled_authorized_m3 = 0.025 * total_siv_m3
        total_authorized_m3 = billed_authorized_m3 + unbilled_authorized_m3
        
        # Water Losses
        total_water_losses_m3 = max(0.0, total_siv_m3 - total_authorized_m3)
        
        # Non-Revenue Water (NRW) = SIV - Billed Authorized
        nrw_volume_m3 = max(0.0, total_siv_m3 - billed_authorized_m3)
        nrw_percentage = (nrw_volume_m3 / max(1.0, total_siv_m3)) * 100.0
        
        # Apparent vs Real Losses
        # Apparent losses: customer meter under-registration (typically ~3.5% of billed) + theft
        apparent_losses_m3 = 0.035 * billed_authorized_m3 + 0.005 * total_siv_m3
        real_physical_losses_m3 = max(0.0, total_water_losses_m3 - apparent_losses_m3)
        
        # Performance Indicators: UARL and ILI
        # Days in dataset
        n_days = max(1.0, len(df) / 96.0)
        # UARL in m3/year scaled to dataset duration:
        # UARL (liters/day) = (18 * Lm + 0.80 * Nc + 25 * Lp) * P
        # Assume Lp ~ 0.015 km per prop * Nc
        lp_km = 0.015 * self.properties_count
        uarl_liters_day = (18.0 * self.mains_length_km + 0.80 * self.properties_count + 25.0 * lp_km) * self.avg_pressure_m
        uarl_m3_day = uarl_liters_day / 1000.0
        total_uarl_period_m3 = uarl_m3_day * n_days
        
        ili = real_physical_losses_m3 / max(1.0, total_uarl_period_m3)
        
        # Classification
        if ili < 1.5:
            ili_rating = "Category A (World Class)"
        elif ili < 4.0:
            ili_rating = "Category B (Good)"
        elif ili < 8.0:
            ili_rating = "Category C (Poor)"
        else:
            ili_rating = "Category D (Critical - Urgent Action Required)"
            
        return {
            "evaluation_days": round(n_days, 1),
            "system_input_volume_m3": round(total_siv_m3, 1),
            "billed_authorized_consumption_m3": round(billed_authorized_m3, 1),
            "unbilled_authorized_consumption_m3": round(unbilled_authorized_m3, 1),
            "total_authorized_m3": round(total_authorized_m3, 1),
            "non_revenue_water_m3": round(nrw_volume_m3, 1),
            "non_revenue_water_pct": round(nrw_percentage, 2),
            "apparent_losses_m3": round(apparent_losses_m3, 1),
            "real_physical_losses_m3": round(real_physical_losses_m3, 1),
            "uarl_period_m3": round(total_uarl_period_m3, 1),
            "infrastructure_leakage_index_ili": round(ili, 2),
            "ili_rating": ili_rating
        }

    def compute_minimum_night_flow_timeseries(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extracts daily Minimum Night Flow (MNF), Net Night Flow (NNF), and night loss trend.
        
        Args:
            df: Time-series DataFrame with timestamp and flow_rate.
            
        Returns:
            DataFrame of daily night flow metrics indexed by date.
        """
        logger.info("Extracting daily Minimum Night Flow (MNF) and Net Night Flow (NNF)...")
        temp = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(temp["timestamp"]):
            temp["timestamp"] = pd.to_datetime(temp["timestamp"])
            
        temp["date"] = temp["timestamp"].dt.date
        temp["hour"] = temp["timestamp"].dt.hour
        
        # Filter strictly for night window: 02:00 to 04:00 AM
        night_df = temp[(temp["hour"] >= self.mnf_start_hour) & (temp["hour"] < self.mnf_end_hour)]
        
        # Legitimate night domestic and commercial consumption (m3/h)
        legitimate_night_prop_m3h = (self.properties_count * self.legitimate_night_use_per_prop_lph) / 1000.0
        known_commercial_night_m3h = 0.50
        total_legitimate_night_m3h = legitimate_night_prop_m3h + known_commercial_night_m3h
        
        # Allowable background joint weeping baseline (m3/h)
        allowable_background_m3h = 0.020 * self.mains_length_km * (self.avg_pressure_m ** 0.5)
        
        # Daily aggregations
        daily_mnf = night_df.groupby("date").agg(
            mnf_flow_min=("flow_rate", "min"),
            mnf_flow_mean=("flow_rate", "mean"),
            night_pressure_mean=("pressure_mean", "mean") if "pressure_mean" in night_df.columns else ("flow_rate", lambda x: np.nan)
        ).reset_index()
        
        daily_mnf["date"] = pd.to_datetime(daily_mnf["date"])
        daily_mnf["legitimate_night_demand"] = round(total_legitimate_night_m3h, 2)
        daily_mnf["allowable_background"] = round(allowable_background_m3h, 2)
        
        # Net Night Flow (NNF) = MNF - Legitimate Night Demand
        daily_mnf["net_night_flow_nnf"] = np.maximum(0.0, daily_mnf["mnf_flow_mean"] - total_legitimate_night_m3h)
        
        # Unexplained Night Loss = NNF - Allowable Background
        daily_mnf["unexplained_night_loss"] = np.maximum(0.0, daily_mnf["net_night_flow_nnf"] - allowable_background_m3h)
        
        # Baseline reference (first 30 days rolling median)
        daily_mnf["baseline_nnf"] = daily_mnf["net_night_flow_nnf"].rolling(window=14, min_periods=1).median()
        daily_mnf["night_loss_anomaly"] = daily_mnf["net_night_flow_nnf"] - daily_mnf["baseline_nnf"]
        
        return daily_mnf
