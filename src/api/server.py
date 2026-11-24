"""Production FastAPI Backend Service for WATERPRINT.

Exposes RESTful endpoints for SCADA telemetry, water balance auditing,
nocturnal minimum night flow (MNF), anomaly detection events,
network topology, sensor health diagnostics, and comparative benchmarks.
Configured with environment-based CORS for secure Vercel frontend integration.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="WATERPRINT Analytics API",
    description="Intelligent Water Loss Detection & Network Analytics REST API",
    version="1.0.0"
)

# CORS Configuration
# Allows setting specific domains via CORS_ORIGINS environment variable
cors_env = os.getenv("CORS_ORIGINS", "*")
origins = [o.strip() for o in cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("data")
REPORTS_DIR = Path("reports")

def _load_json_file(filepath: Path) -> Any:
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Data artifact not found: {filepath.name}")
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _load_csv_file(filepath: Path) -> pd.DataFrame:
    if not filepath.exists():
        raise HTTPException(status_code=404, detail=f"Data artifact not found: {filepath.name}")
    return pd.read_csv(filepath)

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """Health check endpoint for container and API monitoring."""
    return {
        "status": "healthy",
        "service": "WATERPRINT Analytics API",
        "version": "1.0.0",
        "data_status": "loaded" if (REPORTS_DIR / "evaluation_summary.json").exists() else "pending"
    }

@app.get("/api/summary")
def get_kpi_summary() -> Dict[str, Any]:
    """Retrieves high-level executive KPI metrics, water audit totals, and sensor health."""
    summary_path = REPORTS_DIR / "evaluation_summary.json"
    summary_data = _load_json_file(summary_path)
    
    wb = summary_data.get("water_balance_audit", {})
    metrics = summary_data.get("evaluation_metrics", {})
    qc = summary_data.get("sensor_quality_summary", {})
    
    return {
        "system_input_volume_m3": wb.get("system_input_volume_m3", 0.0),
        "billed_authorized_consumption_m3": wb.get("billed_authorized_consumption_m3", 0.0),
        "unbilled_authorized_consumption_m3": wb.get("unbilled_authorized_consumption_m3", 0.0),
        "non_revenue_water_m3": wb.get("non_revenue_water_m3", 0.0),
        "non_revenue_water_pct": wb.get("non_revenue_water_pct", 0.0),
        "real_physical_losses_m3": wb.get("real_physical_losses_m3", 0.0),
        "apparent_losses_m3": wb.get("apparent_losses_m3", 0.0),
        "infrastructure_leakage_index_ili": wb.get("infrastructure_leakage_index_ili", 0.0),
        "ili_rating": wb.get("ili_rating", "N/A"),
        "evaluation_days": wb.get("evaluation_days", 0),
        "total_detected_events": summary_data.get("total_events_detected", 0),
        "benchmark_recall_pct": round(metrics.get("recall", 1.0) * 100.0, 1),
        "benchmark_precision_pct": round(metrics.get("precision", 0.0) * 100.0, 1),
        "mean_detection_delay_hours": metrics.get("mean_detection_delay_hours", 0.0),
        "false_alarms_per_month": metrics.get("false_alarms_per_month", 0.0),
        "data_completeness_pct": qc.get("data_completeness_pct", 100.0),
        "hardware_health_status": qc.get("hardware_health_status", "EXCELLENT"),
        "total_hardware_faults": qc.get("total_sensor_fault_events", 0)
    }

@app.get("/api/flow-pressure")
def get_flow_pressure_timeseries(
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    downsample_step: int = Query(2, description="Downsample factor (e.g. 2 = every 30 mins, 4 = hourly)")
) -> Dict[str, Any]:
    """Retrieves flow and pressure time-series with observed vs expected and 95% uncertainty bounds."""
    ts_parquet = DATA_DIR / "processed" / "processed_network_timeseries.parquet"
    ts_csv = DATA_DIR / "processed" / "processed_network_timeseries.csv"
    
    if ts_parquet.exists():
        df = pd.read_parquet(ts_parquet)
    elif ts_csv.exists():
        df = pd.read_csv(ts_csv)
    else:
        raise HTTPException(status_code=404, detail="Processed time-series dataset not found.")
        
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    
    if start_date:
        df = df[df["timestamp"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["timestamp"] <= pd.to_datetime(end_date) + pd.Timedelta(days=1)]
        
    # Downsample if specified to reduce JSON transmission size
    step = max(1, downsample_step)
    if step > 1:
        df = df.iloc[::step].copy()
        
    records = []
    pressure_cols = [c for c in df.columns if c.startswith("pressure_n")]
    
    for _, row in df.iterrows():
        rec = {
            "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            "flow_rate": float(row["flow_rate"]) if not pd.isna(row["flow_rate"]) else None,
            "expected_flow": float(row["expected_flow"]) if "expected_flow" in row and not pd.isna(row["expected_flow"]) else None,
            "expected_lower_95": float(row["expected_lower_95"]) if "expected_lower_95" in row and not pd.isna(row["expected_lower_95"]) else None,
            "expected_upper_95": float(row["expected_upper_95"]) if "expected_upper_95" in row and not pd.isna(row["expected_upper_95"]) else None,
            "flow_residual": float(row["flow_residual"]) if "flow_residual" in row and not pd.isna(row["flow_residual"]) else None,
            "pressure_mean": float(row["pressure_mean"]) if "pressure_mean" in row and not pd.isna(row["pressure_mean"]) else None,
            "leak_alarm_active": bool(row["leak_alarm_active"]) if "leak_alarm_active" in row and not pd.isna(row["leak_alarm_active"]) else False,
            "is_mnf_window": bool(row["is_mnf_window"]) if "is_mnf_window" in row and not pd.isna(row["is_mnf_window"]) else False,
            "sensor_fault_active": bool(row["sensor_fault_active"]) if "sensor_fault_active" in row and not pd.isna(row["sensor_fault_active"]) else False
        }
        # Add primary sensor pressures
        for p_col in pressure_cols[:4]:
            rec[p_col] = float(row[p_col]) if not pd.isna(row[p_col]) else None
        records.append(rec)
        
    return {
        "count": len(records),
        "downsample_step": step,
        "timeseries": records
    }

@app.get("/api/water-balance")
def get_water_balance() -> Dict[str, Any]:
    """Retrieves standard IWA water balance decomposition and nocturnal MNF progression."""
    summary_path = REPORTS_DIR / "evaluation_summary.json"
    summary_data = _load_json_file(summary_path)
    wb = summary_data.get("water_balance_audit", {})
    
    # Load daily MNF
    mnf_path = DATA_DIR / "processed" / "daily_minimum_night_flow.csv"
    if mnf_path.exists():
        df_mnf = pd.read_csv(mnf_path)
        mnf_records = df_mnf.to_dict(orient="records")
    else:
        mnf_records = []
        
    return {
        "water_balance": wb,
        "daily_minimum_night_flow": mnf_records
    }

@app.get("/api/anomalies")
def get_anomalies() -> Dict[str, Any]:
    """Retrieves verified leak anomaly incidents with candidate zones, nodes, and repair prioritization."""
    events_path = REPORTS_DIR / "anomaly_events.csv"
    if not events_path.exists():
        return {"events": []}
        
    df_events = pd.read_csv(events_path)
    events = []
    
    # Priority weighting dictionary
    sev_weights = {"CRITICAL": 3.0, "HIGH": 2.0, "MEDIUM": 1.0, "LOW": 0.5}
    
    for _, row in df_events.iterrows():
        e = row.to_dict()
        
        # Parse candidate JSON strings
        for field in ["candidate_zones", "candidate_nodes"]:
            if field in e and isinstance(e[field], str):
                try:
                    e[field] = json.loads(e[field])
                except:
                    e[field] = []
                    
        # Compute Repair Prioritization Score (1-100 scale)
        sev_mult = sev_weights.get(e.get("severity", "LOW"), 1.0)
        peak_res = float(e.get("peak_flow_residual_m3h", 0.0))
        dur_hrs = float(e.get("duration_hours", 1.0))
        conf = float(e.get("confidence_score", 0.5))
        
        # Priority score: Higher flow, longer duration, high severity = highest priority
        raw_priority = (peak_res * 2.5) + (sev_mult * 15.0) + (conf * 20.0) + min(20.0, dur_hrs * 0.5)
        e["repair_priority_score"] = int(np.clip(round(raw_priority), 10, 99))
        e["repair_priority_tier"] = "URGENT_P1" if e["repair_priority_score"] >= 75 else ("ELEVATED_P2" if e["repair_priority_score"] >= 50 else "ROUTINE_P3")
        
        events.append(e)
        
    # Sort by repair priority descending
    events = sorted(events, key=lambda x: x["repair_priority_score"], reverse=True)
    return {"events": events}

@app.get("/api/topology")
def get_network_topology() -> Dict[str, Any]:
    """Retrieves full topological node coordinates, pipe links, and DMA zones."""
    topo_path = DATA_DIR / "raw" / "network_topology.json"
    return _load_json_file(topo_path)

@app.get("/api/sensors")
def get_sensor_diagnostics() -> Dict[str, Any]:
    """Retrieves hardware diagnostic fault registry (flatlines, rate spikes, telemetry drops)."""
    summary_path = REPORTS_DIR / "evaluation_summary.json"
    summary_data = _load_json_file(summary_path)
    qc = summary_data.get("sensor_quality_summary", {})
    
    faults_path = DATA_DIR / "processed" / "sensor_fault_registry.csv"
    if faults_path.exists():
        df_faults = pd.read_csv(faults_path)
        faults = df_faults.to_dict(orient="records")
    else:
        faults = []
        
    return {
        "quality_summary": qc,
        "fault_records": faults
    }

@app.get("/api/benchmarks")
def get_benchmark_comparison() -> Dict[str, Any]:
    """Retrieves comparative performance table vs. industry baselines."""
    bench_path = REPORTS_DIR / "benchmark_comparison.csv"
    if not bench_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark comparison table not found.")
        
    df_bench = pd.read_csv(bench_path)
    return {
        "benchmarks": df_bench.to_dict(orient="records")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8088))
    uvicorn.run("src.api.server:app", host="0.0.0.0", port=port, reload=True)
