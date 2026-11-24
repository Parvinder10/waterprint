"""Configuration management module for WATERPRINT."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class SensorQualityConfig(BaseModel):
    flow_min_valid: float = 0.0
    flow_max_valid: float = 500.0
    pressure_min_valid: float = 5.0
    pressure_max_valid: float = 90.0
    max_flatline_consecutive: int = 4
    max_flow_rate_of_change: float = 120.0
    max_pressure_rate_of_change: float = 25.0
    missing_interpolation_limit: int = 4

class FeaturesConfig(BaseModel):
    rolling_windows: List[int] = Field(default_factory=lambda: [4, 12, 24, 96])
    mnf_start_hour: int = 2
    mnf_end_hour: int = 4
    include_lag_features: bool = True
    lag_steps: List[int] = Field(default_factory=lambda: [1, 2, 4, 96, 672])

class BaselineForecasterConfig(BaseModel):
    algorithm: str = "gradient_boosting"
    n_estimators: int = 120
    max_depth: int = 5
    learning_rate: float = 0.08
    prediction_interval_alpha: float = 0.05
    random_state: int = 42

class StatisticalDetectorConfig(BaseModel):
    z_score_threshold: float = 2.75
    rolling_window: int = 96
    cusum_threshold: float = 4.5
    cusum_drift: float = 0.5
    persistence_steps: int = 3

class IsolationForestConfig(BaseModel):
    n_estimators: int = 150
    contamination: float = 0.035
    max_samples: float = 0.8
    random_state: int = 42

class ModelsConfig(BaseModel):
    baseline_forecaster: BaselineForecasterConfig = Field(default_factory=BaselineForecasterConfig)
    statistical_detector: StatisticalDetectorConfig = Field(default_factory=StatisticalDetectorConfig)
    isolation_forest: IsolationForestConfig = Field(default_factory=IsolationForestConfig)

class LocalisationConfig(BaseModel):
    top_k_candidates: int = 3
    hydraulic_resistance_decay: float = 0.15
    min_pressure_drop_sensitivity: float = 0.5

class EvaluationConfig(BaseModel):
    train_split_ratio: float = 0.70
    detection_window_hours: int = 24

class DataConfig(BaseModel):
    raw_dir: str = "data/raw"
    processed_dir: str = "data/processed"
    network_file: str = "data/raw/network_topology.json"
    flow_data_file: str = "data/raw/dma_flow_records.csv"
    pressure_data_file: str = "data/raw/pressure_sensor_records.csv"
    consumption_data_file: str = "data/raw/smart_meter_consumption.csv"
    leak_ground_truth_file: str = "data/raw/leak_ground_truth.csv"
    sample_frequency: str = "15min"
    target_dma: str = "DMA_NORTH"

class AppConfig(BaseModel):
    project_name: str = "WATERPRINT"
    version: str = "1.0.0"
    data: DataConfig = Field(default_factory=DataConfig)
    sensor_quality: SensorQualityConfig = Field(default_factory=SensorQualityConfig)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    localisation: LocalisationConfig = Field(default_factory=LocalisationConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)

def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Loads and validates configuration from YAML or returns defaults.
    
    Args:
        config_path: Path to config YAML file. If None, looks for config/config.yaml.
        
    Returns:
        Validated AppConfig object.
    """
    if config_path is None:
        default_path = Path("config/config.yaml")
        if default_path.exists():
            config_path = str(default_path)
            
    if config_path and Path(config_path).exists():
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                raw_dict = yaml.safe_load(f)
            if raw_dict:
                # Map nested dictionary to AppConfig
                cfg_data = {}
                if "project" in raw_dict:
                    cfg_data["project_name"] = raw_dict["project"].get("name", "WATERPRINT")
                    cfg_data["version"] = raw_dict["project"].get("version", "1.0.0")
                if "data" in raw_dict:
                    cfg_data["data"] = DataConfig(**raw_dict["data"])
                if "sensor_quality" in raw_dict:
                    cfg_data["sensor_quality"] = SensorQualityConfig(**raw_dict["sensor_quality"])
                if "features" in raw_dict:
                    cfg_data["features"] = FeaturesConfig(**raw_dict["features"])
                if "models" in raw_dict:
                    m = raw_dict["models"]
                    cfg_data["models"] = ModelsConfig(
                        baseline_forecaster=BaselineForecasterConfig(**m.get("baseline_forecaster", {})),
                        statistical_detector=StatisticalDetectorConfig(**m.get("statistical_detector", {})),
                        isolation_forest=IsolationForestConfig(**m.get("isolation_forest", {}))
                    )
                if "localisation" in raw_dict:
                    cfg_data["localisation"] = LocalisationConfig(**raw_dict["localisation"])
                if "evaluation" in raw_dict:
                    cfg_data["evaluation"] = EvaluationConfig(**raw_dict["evaluation"])
                return AppConfig(**cfg_data)
        except Exception:
            pass  # Fallback to default initialized AppConfig
            
    return AppConfig()
