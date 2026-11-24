"""Integration tests for WATERPRINT API, CORS, and Vercel Frontend build."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from src.api.server import app

client = TestClient(app)

def test_api_health():
    """Verifies health check endpoint returns 200 and healthy status."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "WATERPRINT Analytics API"

def test_api_summary():
    """Verifies executive summary endpoint returns complete water balance & sensor metrics."""
    res = client.get("/api/summary")
    assert res.status_code == 200
    data = res.json()
    assert "system_input_volume_m3" in data
    assert "non_revenue_water_pct" in data
    assert "infrastructure_leakage_index_ili" in data
    assert "total_detected_events" in data
    assert data["system_input_volume_m3"] > 0
    assert data["data_completeness_pct"] >= 95.0

def test_api_flow_pressure():
    """Verifies flow and pressure time-series endpoint with downsampling."""
    res = client.get("/api/flow-pressure?downsample_step=5")
    assert res.status_code == 200
    data = res.json()
    assert "timeseries" in data
    assert data["count"] > 0
    first_pt = data["timeseries"][0]
    assert "flow_rate" in first_pt
    assert "pressure_mean" in first_pt
    assert "leak_alarm_active" in first_pt

def test_api_water_balance():
    """Verifies IWA water balance and daily minimum night flow."""
    res = client.get("/api/water-balance")
    assert res.status_code == 200
    data = res.json()
    assert "water_balance" in data
    assert "daily_minimum_night_flow" in data
    assert len(data["daily_minimum_night_flow"]) > 0

def test_api_anomalies_and_repair_prioritization():
    """Verifies anomaly detection events, candidate areas, and repair prioritization scores."""
    res = client.get("/api/anomalies")
    assert res.status_code == 200
    data = res.json()
    assert "events" in data
    assert len(data["events"]) > 0
    
    first_evt = data["events"][0]
    assert "event_id" in first_evt
    assert "repair_priority_score" in first_evt
    assert 10 <= first_evt["repair_priority_score"] <= 100
    assert "repair_priority_tier" in first_evt
    assert first_evt["repair_priority_tier"] in ["URGENT_P1", "ELEVATED_P2", "ROUTINE_P3"]
    assert "candidate_zones" in first_evt

def test_api_topology():
    """Verifies network topology returns nodes, pipes, and coordinates."""
    res = client.get("/api/topology")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "pipes" in data
    assert len(data["nodes"]) == 33
    assert len(data["pipes"]) == 53
    # Check coordinates exist
    assert "coordinates" in data["nodes"][0]

def test_api_sensors():
    """Verifies sensor diagnostic registry separates hardware faults from leaks."""
    res = client.get("/api/sensors")
    assert res.status_code == 200
    data = res.json()
    assert "quality_summary" in data
    assert "fault_records" in data

def test_api_cors_preflight():
    """Verifies CORS preflight headers support Vercel cross-origin requests."""
    res = client.options(
        "/api/summary",
        headers={
            "Origin": "https://waterprint.vercel.app",
            "Access-Control-Request-Method": "GET"
        }
    )
    assert res.status_code == 200
    assert "access-control-allow-origin" in res.headers

def test_frontend_dist_artifacts():
    """Verifies that Vite built frontend artifacts exist and are non-empty."""
    dist_dir = Path("frontend/dist")
    assert dist_dir.exists(), "frontend/dist directory must exist"
    assert (dist_dir / "index.html").exists(), "index.html must exist in dist"
    assert (dist_dir / "assets").exists(), "assets folder must exist in dist"
    
    html = (dist_dir / "index.html").read_text(encoding="utf-8")
    assert "WATERPRINT" in html
    assert '<div id="root"></div>' in html

def test_vercel_json_configuration():
    """Verifies vercel.json contains SPA rewrites and clean URLs."""
    v_frontend = Path("frontend/vercel.json")
    assert v_frontend.exists()
    cfg_f = json.loads(v_frontend.read_text(encoding="utf-8"))
    assert "rewrites" in cfg_f
    assert cfg_f["rewrites"][0]["destination"] == "/index.html"
    
    v_root = Path("vercel.json")
    assert v_root.exists()
    cfg_r = json.loads(v_root.read_text(encoding="utf-8"))
    assert "buildCommand" in cfg_r
    assert "outputDirectory" in cfg_r
