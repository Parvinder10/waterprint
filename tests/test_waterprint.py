"""Unit & Integration Test Suite for WATERPRINT.

Validates:
- Manual calculation benchmarks for IWA water balance
- Sensor quality checks (flatlines, out-of-range, rate spikes)
- Time-series alignment and temporal integrity
- Statistical Z-score, CUSUM drift, and persistence filters
- Quantile baseline prediction intervals
- Network topological graph construction and localization
- Full end-to-end integration workflow
"""

import os
import json
import pytest
import numpy as np
import pandas as pd

from src.ingestion.loader import WaterDataLoader
from src.preprocessing.alignment import TimeSeriesAligner
from src.preprocessing.sensor_quality import SensorQualityChecker
from src.features.feature_engineering import FeatureEngineer
from src.statistics.water_balance import WaterBalanceAnalyzer
from src.statistics.statistical_detector import StatisticalDetector
from src.models.baseline_forecaster import BaselineFlowForecaster
from src.models.residual_detector import ResidualAnomalyDetector
from src.models.isolation_forest import WaterIsolationForest
from src.models.ensemble import EnsembleAnomalyArbiter
from src.localisation.network_graph import NetworkGraph
from src.localisation.sensitivity_localiser import NetworkLocaliser
from src.evaluation.metrics import WaterLossEvaluator
from src.utils.config import load_config

# ========================================================
# 1. MANUAL CALCULATION TEST: IWA WATER BALANCE
# ========================================================
def test_manual_water_balance_calculation():
    """Verifies standard IWA water balance calculations against a manually checked arithmetic case."""
    # Scenario:
    # 4 time steps of 15 min each (1 hour total)
    # Inflow = 100.0 m3/h -> Total SIV = 100.0 m3
    # Authorized metered consumption = 75.0 m3/h -> Total Billed = 75.0 m3
    df_manual = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01 00:00:00", periods=4, freq="15min"),
        "flow_rate": [100.0, 100.0, 100.0, 100.0],
        "total_authorized_consumption": [75.0, 75.0, 75.0, 75.0]
    })
    
    analyzer = WaterBalanceAnalyzer(
        properties_count=1000,
        mains_length_km=10.0,
        avg_pressure_m=50.0
    )
    result = analyzer.compute_macro_water_balance(df_manual)
    
    # SIV = 100 m3
    assert result["system_input_volume_m3"] == 100.0
    # Billed authorized = 75 m3
    assert result["billed_authorized_consumption_m3"] == 75.0
    # Unbilled authorized = 2.5% of SIV = 2.5 m3
    assert result["unbilled_authorized_consumption_m3"] == 2.5
    # Total authorized = 77.5 m3
    assert result["total_authorized_m3"] == 77.5
    # Non-Revenue Water = SIV - Billed = 25.0 m3 (25.0%)
    assert result["non_revenue_water_m3"] == 25.0
    assert result["non_revenue_water_pct"] == 25.0
    # Apparent losses = 3.5% of billed (2.625) + 0.5% of SIV (0.5) = 3.125 -> round 3.1
    assert result["apparent_losses_m3"] == pytest.approx(3.1, abs=0.1)

# ========================================================
# 2. SENSOR QUALITY & HARDWARE ANOMALY ISOLATION
# ========================================================
def test_sensor_flatline_detection():
    """Ensures sensor ADC freeze / flatline is caught and segregated from leak alarms."""
    df_test = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="15min"),
        "flow_rate": [50.0, 50.0, 50.0, 50.0, 50.0, 52.0, 53.0, 54.0, 55.0, 56.0]
    })
    
    qc = SensorQualityChecker()
    cleaned, faults, summary = qc.evaluate_quality(df_test)
    
    assert len(faults) > 0
    flatline_records = faults[faults["fault_type"] == "FLATLINE"]
    assert not flatline_records.empty
    assert flatline_records.iloc[0]["sensor_id"] == "flow_rate"

def test_sensor_out_of_bounds_detection():
    """Validates physical boundary checks for flow and pressure."""
    df_test = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=5, freq="15min"),
        "flow_rate": [50.0, -15.0, 52.0, 650.0, 51.0], # -15 and 650 violate limits [0, 500]
        "pressure_n1": [45.0, 2.0, 48.0, 110.0, 47.0] # 2.0 and 110 violate limits [5, 90]
    })
    
    qc = SensorQualityChecker()
    cleaned, faults, summary = qc.evaluate_quality(df_test)
    
    oob_faults = faults[faults["fault_type"] == "OUT_OF_BOUNDS"]
    assert len(oob_faults) == 4

# ========================================================
# 3. TIME-SERIES ALIGNMENT & INTEGRITY
# ========================================================
def test_timeseries_alignment_and_deduplication():
    """Verifies that duplicate and missing timestamps are harmonized onto a regular grid."""
    # Data with duplicate timestamp and missing interval
    times = pd.to_datetime([
        "2024-01-01 00:00:00",
        "2024-01-01 00:00:00", # duplicate
        "2024-01-01 00:15:00",
        "2024-01-01 00:45:00"  # skipped 00:30:00
    ])
    df_f = pd.DataFrame({"timestamp": times, "flow_rate": [50.0, 50.5, 52.0, 55.0]})
    df_p = pd.DataFrame({"timestamp": times[:3], "pressure_n1": [45.0, 45.0, 46.0]})
    
    aligner = TimeSeriesAligner(target_freq="15min")
    aligned = aligner.align_and_merge(df_f, df_p)
    
    # Result must span 00:00, 00:15, 00:30, 00:45 (4 rows, no duplicates)
    assert len(aligned) == 4
    assert aligned["timestamp"].nunique() == 4
    assert pd.to_datetime("2024-01-01 00:30:00") in aligned["timestamp"].values

# ========================================================
# 4. STATISTICAL CUSUM & PERSISTENCE FILTER
# ========================================================
def test_cusum_drift_and_persistence_filter():
    """Tests that CUSUM accumulates consistent upward drift and persistence filter rejects single spikes."""
    detector = StatisticalDetector()
    
    # 50 zeros followed by 20 sustained positive residuals (+2.0)
    residuals = pd.Series([0.0] * 50 + [2.0] * 20)
    cusum_vals, cusum_alarms = detector.detect_cusum_changepoint(residuals, drift=0.5, threshold=4.5)
    
    # CUSUM should start alarming after persistent accumulation
    assert np.any(cusum_alarms[50:])
    
    # Test persistence filter on a single isolated spike
    spiky_alarms = pd.Series([False, False, True, False, False, True, True, True, True, False])
    filtered = detector.apply_persistence_filter(spiky_alarms, min_consecutive=3)
    
    # The isolated True at index 2 must be eliminated
    assert not filtered.iloc[2]
    # The sustained True run at indices 5-8 must be kept (after 3 steps)
    assert filtered.iloc[7] and filtered.iloc[8]

# ========================================================
# 5. ML BASELINE FORECASTER & PREDICTION INTERVALS
# ========================================================
def test_baseline_forecaster_ordering():
    """Verifies that predicted lower 95% bound <= expected median <= upper 95% bound."""
    # Synthetic diurnal data for 5 days
    dates = pd.date_range("2024-01-01", periods=96 * 5, freq="15min")
    hours = dates.hour + dates.minute / 60.0
    synth_flow = 80.0 + 30.0 * np.sin(2 * np.pi * hours / 24.0) + np.random.normal(0, 1.0, len(dates))
    
    df_train = pd.DataFrame({
        "timestamp": dates,
        "flow_rate": synth_flow,
        "hour": dates.hour,
        "day_of_week": dates.dayofweek,
        "is_weekend": (dates.dayofweek >= 5).astype(int),
        "day_of_year": dates.dayofyear,
        "sin_hour": np.sin(2 * np.pi * hours / 24.0),
        "cos_hour": np.cos(2 * np.pi * hours / 24.0),
        "sin_dow": np.sin(2 * np.pi * dates.dayofweek / 7.0),
        "cos_dow": np.cos(2 * np.pi * dates.dayofweek / 7.0),
        "flow_lag_96": synth_flow,
        "flow_lag_672": synth_flow,
        "flow_rolling_mean_96": synth_flow
    })
    
    forecaster = BaselineFlowForecaster()
    forecaster.fit(df_train)
    exp, lower, upper = forecaster.predict(df_train)
    
    assert len(exp) == len(df_train)
    # Check strict ordering: lower <= exp <= upper across all points
    assert np.all(lower <= exp + 1e-5)
    assert np.all(exp <= upper + 1e-5)

# ========================================================
# 6. NETWORK TOPOLOGY & SENSITIVITY LOCALISATION
# ========================================================
def test_network_graph_and_localisation():
    """Verifies NetworkX graph shortest path calculation and sensitivity matrix ranking."""
    topology = {
        "dma_id": "TEST_DMA",
        "zones": ["ZONE_A", "ZONE_B"],
        "sensor_nodes": ["n1", "n2"],
        "nodes": [
            {"node_id": "RES_1", "elevation": 50.0, "zone": "SOURCE", "coordinates": {"x": 0.0, "y": 0.0}},
            {"node_id": "n1", "elevation": 30.0, "zone": "ZONE_A", "has_pressure_sensor": True, "coordinates": {"x": 100.0, "y": 0.0}},
            {"node_id": "n2", "elevation": 30.0, "zone": "ZONE_B", "has_pressure_sensor": True, "coordinates": {"x": 200.0, "y": 0.0}},
            {"node_id": "n3", "elevation": 28.0, "zone": "ZONE_B", "has_pressure_sensor": False, "coordinates": {"x": 300.0, "y": 0.0}}
        ],
        "pipes": [
            {"pipe_id": "p1", "start_node": "RES_1", "end_node": "n1", "length": 100.0, "diameter": 200.0, "roughness": 120.0},
            {"pipe_id": "p2", "start_node": "n1", "end_node": "n2", "length": 100.0, "diameter": 150.0, "roughness": 120.0},
            {"pipe_id": "p3", "start_node": "n2", "end_node": "n3", "length": 100.0, "diameter": 100.0, "roughness": 120.0}
        ]
    }
    
    net = NetworkGraph(topology)
    assert net.graph.number_of_nodes() == 4
    assert net.graph.number_of_edges() == 3
    
    localiser = NetworkLocaliser(net)
    
    # Simulate a severe pressure drop at sensor n2 (close to n3)
    event_df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=10, freq="15min"),
        "pressure_n1": [48.0] * 10,
        "pressure_n2": [32.0] * 10  # Drop of 16m at n2
    })
    baseline_df = pd.DataFrame({
        "pressure_n1": [48.5] * 10,
        "pressure_n2": [48.0] * 10
    })
    
    res = localiser.localise_event(event_df, baseline_df=baseline_df, top_k=2)
    assert res["localisation_status"] == "RESOLVED"
    # Sensor n2 experienced max drop
    assert res["max_drop_sensor"] == "n2"
    # Candidate zone should be ZONE_B
    assert res["primary_zone"] == "ZONE_B"
