"""Data Ingestion Module for WATERPRINT.

Handles ingestion, schema validation, and type casting for flow, pressure,
smart-meter consumption, network topology, and ground truth files.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
from src.utils.logging import logger
from src.utils.exceptions import DataIngestionError

class WaterDataLoader:
    """Manages loading and initial validation of raw water network files."""
    
    def __init__(self, data_dir: str = "data/raw"):
        self.data_dir = Path(data_dir)
        
    def load_flow_records(self, filename: str = "dma_flow_records.csv") -> pd.DataFrame:
        """Loads and validates DMA inlet flow records."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise DataIngestionError(f"Flow data file not found at: {filepath}")
            
        logger.info(f"Loading flow records from {filepath}...")
        df = pd.read_csv(filepath)
        required_cols = {"timestamp", "dma_id", "flow_rate"}
        if not required_cols.issubset(df.columns):
            raise DataIngestionError(f"Missing required columns in flow data: {required_cols - set(df.columns)}")
            
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def load_pressure_records(self, filename: str = "pressure_sensor_records.csv") -> pd.DataFrame:
        """Loads and validates nodal pressure transducer records."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise DataIngestionError(f"Pressure data file not found at: {filepath}")
            
        logger.info(f"Loading pressure records from {filepath}...")
        df = pd.read_csv(filepath)
        if "timestamp" not in df.columns:
            raise DataIngestionError("Pressure data missing 'timestamp' column.")
            
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def load_consumption_records(self, filename: str = "smart_meter_consumption.csv") -> pd.DataFrame:
        """Loads customer smart meter consumption data."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise DataIngestionError(f"Consumption file not found at: {filepath}")
            
        df = pd.read_csv(filepath)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)
        return df

    def load_leak_ground_truth(self, filename: str = "leak_ground_truth.csv") -> pd.DataFrame:
        """Loads ground truth leak scenarios used for model evaluation."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            logger.warning(f"No ground truth leak file found at {filepath}. Evaluation against ground truth will be skipped.")
            return pd.DataFrame()
            
        df = pd.read_csv(filepath)
        if "start_time" in df.columns:
            df["start_time"] = pd.to_datetime(df["start_time"])
        if "end_time" in df.columns:
            df["end_time"] = pd.to_datetime(df["end_time"])
        return df

    def load_topology(self, filename: str = "network_topology.json") -> Dict[str, Any]:
        """Loads network topology JSON definition."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise DataIngestionError(f"Network topology file not found at: {filepath}")
            
        with open(filepath, "r", encoding="utf-8") as f:
            topology = json.load(f)
            
        if "nodes" not in topology or "pipes" not in topology:
            raise DataIngestionError("Invalid topology: Must contain 'nodes' and 'pipes' keys.")
            
        return topology
