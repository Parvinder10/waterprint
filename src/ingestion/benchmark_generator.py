"""Benchmark dataset generator for WATERPRINT based on the BattLeDIM / L-Town network specifications.

Generates realistic hydraulic time-series (DMA flow, nodal pressure, smart-meter consumption)
with authentic diurnal curves, hydraulic Hazen-Williams head losses, sensor noise,
isolated sensor telemetry glitches, and ground-truth leak events.
"""

import json
import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from src.utils.logging import logger

def build_benchmark_topology() -> dict:
    """Constructs a realistic 32-node District Metered Area (DMA_NORTH) network topology.
    
    Returns:
        Dictionary representation of the network topology with nodes, pipes, and zones.
    """
    # 32 Junction Nodes with elevations and coordinates
    # Arranged into 4 operational zones: ZONE_NORTH_WEST, ZONE_NORTH_EAST, ZONE_CENTRAL, ZONE_COMMERCIAL
    zones = ["ZONE_NORTH_WEST", "ZONE_NORTH_EAST", "ZONE_CENTRAL", "ZONE_COMMERCIAL"]
    sensor_nodes = {"n1", "n5", "n9", "n14", "n18", "n22", "n27", "n31"}
    
    nodes = []
    # Grid coordinates around (500000, 4200000)
    for i in range(1, 33):
        nid = f"n{i}"
        row = (i - 1) // 8
        col = (i - 1) % 8
        x = 542000.0 + col * 450.0 + np.sin(i) * 50.0
        y = 4120000.0 + row * 400.0 + np.cos(i) * 40.0
        
        # Zone assignment
        if row < 2 and col < 4:
            zone = "ZONE_NORTH_WEST"
        elif row < 2 and col >= 4:
            zone = "ZONE_NORTH_EAST"
        elif row >= 2 and col < 4:
            zone = "ZONE_COMMERCIAL"
        else:
            zone = "ZONE_CENTRAL"
            
        elevation = 35.0 + float(np.round(15.0 * np.sin(0.4 * i) + 5.0 * (row + 1), 1))
        base_demand = float(np.round(1.5 + 0.8 * (i % 5), 2))
        
        nodes.append({
            "node_id": nid,
            "elevation": elevation,
            "base_demand": base_demand,
            "coordinates": {"x": float(np.round(x, 1)), "y": float(np.round(y, 1))},
            "zone": zone,
            "has_pressure_sensor": nid in sensor_nodes,
            "sensor_id": f"p_{nid}" if nid in sensor_nodes else None
        })
        
    # Reservoir inlet node
    nodes.insert(0, {
        "node_id": "RES_1",
        "elevation": 75.0,
        "base_demand": 0.0,
        "coordinates": {"x": 541500.0, "y": 4120500.0},
        "zone": "SOURCE",
        "has_pressure_sensor": True,
        "sensor_id": "p_res1"
    })

    # Pipes forming a looped distribution grid
    pipes = []
    pid = 100
    # Connect reservoir to n1
    pipes.append({
        "pipe_id": f"p{pid}",
        "start_node": "RES_1",
        "end_node": "n1",
        "length": 600.0,
        "diameter": 300.0,
        "roughness": 120.0,
        "material": "Ductile_Iron"
    })
    pid += 1
    
    # Horizontal grid connections
    for row in range(4):
        for col in range(7):
            u = row * 8 + col + 1
            v = u + 1
            pipes.append({
                "pipe_id": f"p{pid}",
                "start_node": f"n{u}",
                "end_node": f"n{v}",
                "length": float(np.round(420.0 + 30.0 * np.sin(pid), 1)),
                "diameter": 200.0 if row in (0, 3) else 150.0,
                "roughness": 115.0,
                "material": "PVC" if row >= 2 else "Ductile_Iron"
            })
            pid += 1

    # Vertical grid connections
    for row in range(3):
        for col in range(8):
            u = row * 8 + col + 1
            v = u + 8
            pipes.append({
                "pipe_id": f"p{pid}",
                "start_node": f"n{u}",
                "end_node": f"n{v}",
                "length": float(np.round(380.0 + 25.0 * np.cos(pid), 1)),
                "diameter": 150.0 if col in (0, 7) else 100.0,
                "roughness": 110.0,
                "material": "MDPE"
            })
            pid += 1

    # Pump at reservoir
    pumps = [{
        "pump_id": "PUMP_1",
        "inlet_node": "RES_1",
        "outlet_node": "n1",
        "power_kw": 55.0,
        "status": "RUNNING"
    }]

    return {
        "dma_id": "DMA_NORTH",
        "name": "L-Town North District Metered Area",
        "nodes": nodes,
        "pipes": pipes,
        "pumps": pumps,
        "sensor_nodes": sorted(list(sensor_nodes)),
        "zones": zones
    }

def generate_benchmark_data(
    start_date: str = "2024-01-01",
    days: int = 180,
    output_dir: str = "data/raw",
    random_seed: int = 42
):
    """Generates aligned time-series for flow, pressure, smart meters, and leak ground truth."""
    np.random.seed(random_seed)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Network Topology
    topology = build_benchmark_topology()
    topo_path = os.path.join(output_dir, "network_topology.json")
    with open(topo_path, "w", encoding="utf-8") as f:
        json.dump(topology, f, indent=2)
    logger.info(f"Generated network topology: {topo_path} with {len(topology['nodes'])} nodes, {len(topology['pipes'])} pipes.")

    # 2. Time Index (15-min intervals)
    freq = "15min"
    date_range = pd.date_range(start=start_date, periods=days * 96, freq=freq, name="timestamp")
    n_steps = len(date_range)
    logger.info(f"Generating {n_steps} time steps ({days} days at 15-min frequency)...")

    # Diurnal Profile components
    hours = date_range.hour.values + date_range.minute.values / 60.0
    day_of_week = date_range.dayofweek.values
    is_weekend = (day_of_week >= 5).astype(float)
    day_of_year = date_range.dayofyear.values

    # Realistic Diurnal Curve:
    # Morning peak around 07:30 (Gaussian), Evening peak around 19:30, Minimum Night Flow between 02:00-04:00
    morning_peak = 1.35 * np.exp(-0.5 * ((hours - 7.5) / 1.5) ** 2)
    evening_peak = 1.20 * np.exp(-0.5 * ((hours - 19.5) / 1.8) ** 2)
    afternoon_plateau = 0.75 * np.exp(-0.5 * ((hours - 13.0) / 4.0) ** 2)
    base_nocturnal = 0.28  # legitimate minimum night base flow multiplier

    diurnal_multiplier = base_nocturnal + morning_peak + evening_peak + afternoon_plateau
    # Weekend shift: peak starts 1.5 hours later
    weekend_shift = 0.15 * np.exp(-0.5 * ((hours - 9.0) / 2.0) ** 2) * is_weekend
    diurnal_multiplier += weekend_shift

    # Seasonal temperature modulation (summer has ~18% higher demand than winter)
    seasonal_factor = 1.0 + 0.18 * np.sin(2 * np.pi * (day_of_year - 80) / 365.25)

    # Base nominal DMA inflow (m3/h)
    nominal_base_inflow = 85.0
    clean_flow = nominal_base_inflow * diurnal_multiplier * seasonal_factor
    # Random realistic noise (+- 1.5%)
    measurement_noise = np.random.normal(0, 0.015 * clean_flow, size=n_steps)
    inflow = clean_flow + measurement_noise

    # 3. Ground Truth Leak Injection
    # Training period: first 70% of days (days 0 to 126) is strictly leak-free!
    # Test period: remaining 30% of days (days 126 to 180) contains 5 distinct leak scenarios.
    split_idx = int(0.70 * n_steps)
    test_start_date = date_range[split_idx]
    logger.info(f"Chronological split at step {split_idx} ({test_start_date}). Test set has leaks.")

    leak_events = [
        {
            "leak_id": "LK_2024_001",
            "target_node_id": "n14",
            "target_pipe_id": "p122",
            "dma_id": "DMA_NORTH",
            "start_day": 133,
            "start_hour": 3,
            "duration_hours": 60,
            "leak_flow_rate": 14.5,
            "leak_type": "BURST",
            "pipe_diameter": 150.0
        },
        {
            "leak_id": "LK_2024_002",
            "target_node_id": "n27",
            "target_pipe_id": "p145",
            "dma_id": "DMA_NORTH",
            "start_day": 144,
            "start_hour": 14,
            "duration_hours": 96,
            "leak_flow_rate": 8.0,
            "leak_type": "INCIPIENT",
            "pipe_diameter": 100.0
        },
        {
            "leak_id": "LK_2024_003",
            "target_node_id": "n9",
            "target_pipe_id": "p115",
            "dma_id": "DMA_NORTH",
            "start_day": 155,
            "start_hour": 22,
            "duration_hours": 48,
            "leak_flow_rate": 18.2,
            "leak_type": "BURST",
            "pipe_diameter": 200.0
        },
        {
            "leak_id": "LK_2024_004",
            "target_node_id": "n5",
            "target_pipe_id": "p108",
            "dma_id": "DMA_NORTH",
            "start_day": 164,
            "start_hour": 4,
            "duration_hours": 80,
            "leak_flow_rate": 6.5,
            "leak_type": "INCIPIENT",
            "pipe_diameter": 150.0
        },
        {
            "leak_id": "LK_2024_005",
            "target_node_id": "n22",
            "target_pipe_id": "p138",
            "dma_id": "DMA_NORTH",
            "start_day": 173,
            "start_hour": 1,
            "duration_hours": 52,
            "leak_flow_rate": 12.0,
            "leak_type": "BURST",
            "pipe_diameter": 150.0
        }
    ]

    leak_flow_vector = np.zeros(n_steps)
    leak_records = []

    for lk in leak_events:
        start_step = lk["start_day"] * 96 + int(lk["start_hour"] * 4)
        duration_steps = int(lk["duration_hours"] * 4)
        end_step = min(start_step + duration_steps, n_steps)
        
        t_start = date_range[start_step]
        t_end = date_range[end_step - 1]
        
        lk_rec = {
            "leak_id": lk["leak_id"],
            "target_node_id": lk["target_node_id"],
            "target_pipe_id": lk["target_pipe_id"],
            "dma_id": lk["dma_id"],
            "start_time": t_start.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": t_end.strftime("%Y-%m-%d %H:%M:%S"),
            "leak_flow_rate": lk["leak_flow_rate"],
            "leak_type": lk["leak_type"],
            "pipe_diameter": lk["pipe_diameter"]
        }
        leak_records.append(lk_rec)
        
        # Inject leak flow profile
        if lk["leak_type"] == "BURST":
            # Abrupt burst reaches full discharge rapidly within 30 mins
            profile = np.ones(end_step - start_step) * lk["leak_flow_rate"]
            ramp = min(2, len(profile))
            profile[:ramp] = np.linspace(0.5 * lk["leak_flow_rate"], lk["leak_flow_rate"], ramp)
        else:
            # Incipient leak grows linearly over 24 hours (96 steps) to peak discharge
            ramp_len = min(96, end_step - start_step)
            ramp = np.linspace(0.15 * lk["leak_flow_rate"], lk["leak_flow_rate"], ramp_len)
            profile = np.ones(end_step - start_step) * lk["leak_flow_rate"]
            profile[:ramp_len] = ramp
            
        leak_flow_vector[start_step:end_step] += profile

    # Add leak flow to total inflow
    total_inflow = inflow + leak_flow_vector

    # 4. Sensor Telemetry Faults (Distinct from leaks!)
    # Telemetry flatline on day 45 (sensor freeze for 4 steps)
    meter_status = ["OK"] * n_steps
    flatline_idx = 45 * 96 + 32
    for s in range(4):
        total_inflow[flatline_idx + s] = total_inflow[flatline_idx]
        meter_status[flatline_idx + s] = "FLATLINE"
        
    # Transient electrical spike on day 82 (single step spike of +80 m3/h)
    spike_idx = 82 * 96 + 48
    total_inflow[spike_idx] += 80.0
    meter_status[spike_idx] = "RATE_SPIKE"

    # Packet drop on day 110 (missing NaN for 2 steps)
    drop_idx = 110 * 96 + 20
    total_inflow[drop_idx:drop_idx + 2] = np.nan
    meter_status[drop_idx] = "DROP"
    meter_status[drop_idx + 1] = "DROP"

    # Accumulated flow (m3)
    valid_flow_for_cum = np.nan_to_num(total_inflow, nan=nominal_base_inflow)
    accumulated_flow = np.cumsum(valid_flow_for_cum * 0.25) # 15 min = 0.25h

    # Create DMA Flow DataFrame
    df_flow = pd.DataFrame({
        "timestamp": date_range.strftime("%Y-%m-%d %H:%M:%S"),
        "dma_id": "DMA_NORTH",
        "flow_rate": np.round(total_inflow, 2),
        "flow_accumulated": np.round(accumulated_flow, 2),
        "meter_status": meter_status
    })
    flow_csv = os.path.join(output_dir, "dma_flow_records.csv")
    df_flow.to_csv(flow_csv, index=False)
    logger.info(f"Saved DMA flow records: {flow_csv} ({len(df_flow)} records)")

    # 5. Smart Meter Customer Consumption (Authorized Demand)
    # Customer billed demand follows the uncompromised clean demand pattern minus background loss
    unaccounted_background = 4.2 # m3/h legitimate unavoidable background loss
    authorized_demand = np.maximum(0.0, clean_flow - unaccounted_background + np.random.normal(0, 0.8, size=n_steps))
    
    df_consumption = pd.DataFrame({
        "timestamp": date_range.strftime("%Y-%m-%d %H:%M:%S"),
        "dma_id": "DMA_NORTH",
        "customer_category": "RESIDENTIAL",
        "metered_consumption": np.round(authorized_demand * 0.85, 2), # 85% residential
        "commercial_consumption": np.round(authorized_demand * 0.15, 2), # 15% commercial
        "active_meters_count": 2450
    })
    consumption_csv = os.path.join(output_dir, "smart_meter_consumption.csv")
    df_consumption.to_csv(consumption_csv, index=False)
    logger.info(f"Saved smart meter consumption: {consumption_csv}")

    # 6. Pressure Sensor Records across Monitored Junctions
    # Hazen-Williams frictional head loss: h_loss = r * Q^1.852
    # Baseline reservoir pressure is 65 meters head.
    # When flow increases, friction head loss increases, so pressure drops.
    # When a leak occurs near node j, pressure at node j drops significantly.
    base_head = 65.0
    pressure_sensor_nodes = topology["sensor_nodes"]
    
    pressure_data = {}
    pressure_data["timestamp"] = date_range.strftime("%Y-%m-%d %H:%M:%S")
    
    # Hydraulic distance from reservoir n1 for each sensor node
    hydraulic_distances = {
        "n1": 1.0, "n5": 2.2, "n9": 2.8, "n14": 3.6,
        "n18": 4.1, "n22": 4.8, "n27": 5.4, "n31": 6.2
    }
    
    # Friction head loss coefficient
    friction_coeff = 0.0018

    # Ground elevations
    node_elevations = {n["node_id"]: n["elevation"] for n in topology["nodes"]}
    ref_elevation = 40.0

    for sn in pressure_sensor_nodes:
        dist = hydraulic_distances.get(sn, 3.5)
        elev_diff = node_elevations.get(sn, 40.0) - ref_elevation
        
        # Nominal pressure head at this sensor
        # h = base_head - elev_diff - friction_coeff * dist * (total_inflow ** 1.852)
        nominal_p = base_head - elev_diff - (friction_coeff * dist * (clean_flow ** 1.852))
        
        # Leak pressure drop effect:
        # If leak is near this sensor node, calculate localized pressure depression
        leak_p_drop = np.zeros(n_steps)
        for lk in leak_events:
            target = lk["target_node_id"]
            start_step = lk["start_day"] * 96 + int(lk["start_hour"] * 4)
            duration_steps = int(lk["duration_hours"] * 4)
            end_step = min(start_step + duration_steps, n_steps)
            
            # Sensitivity based on graph distance
            if sn == target:
                sensitivity = 0.28 # Highest sensitivity if sensor is at leak node
            elif abs(int(sn[1:]) - int(target[1:])) <= 4:
                sensitivity = 0.16 # High sensitivity if nearby
            else:
                sensitivity = 0.05 # Attenuated sensitivity if distant
                
            leak_p_drop[start_step:end_step] += sensitivity * leak_flow_vector[start_step:end_step]
            
        sensor_noise = np.random.normal(0, 0.12, size=n_steps) # +-0.12m noise
        p_head = nominal_p - leak_p_drop + sensor_noise
        
        # Keep physical boundaries
        p_head = np.clip(p_head, 12.0, 85.0)
        pressure_data[f"pressure_{sn}"] = np.round(p_head, 2)

    df_pressure = pd.DataFrame(pressure_data)
    pressure_csv = os.path.join(output_dir, "pressure_sensor_records.csv")
    df_pressure.to_csv(pressure_csv, index=False)
    logger.info(f"Saved pressure records: {pressure_csv} ({len(pressure_sensor_nodes)} sensors)")

    # 7. Leak Ground Truth CSV
    df_leaks = pd.DataFrame(leak_records)
    leaks_csv = os.path.join(output_dir, "leak_ground_truth.csv")
    df_leaks.to_csv(leaks_csv, index=False)
    logger.info(f"Saved ground truth leaks: {leaks_csv} ({len(df_leaks)} events)")

    logger.info("Benchmark data generation completed successfully!")
    return {
        "flow_file": flow_csv,
        "pressure_file": pressure_csv,
        "consumption_file": consumption_csv,
        "leaks_file": leaks_csv,
        "topology_file": topo_path
    }

if __name__ == "__main__":
    generate_benchmark_data()
