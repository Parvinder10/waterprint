"""End-to-End Orchestration Pipeline for WATERPRINT.

Executes the complete data ingestion, preprocessing, sensor health validation,
feature engineering, water balance auditing, probabilistic baseline forecasting,
ensemble anomaly detection, network localization, and benchmarking workflow.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

from src.utils.logging import logger
from src.utils.config import AppConfig, load_config
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
from src.evaluation.benchmark_comparison import BenchmarkComparator

class WaterprintPipeline:
    """Master workflow orchestrator for WATERPRINT intelligent water loss analytics."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        self.cfg = config or load_config()
        self.data_loader = WaterDataLoader(data_dir=self.cfg.data.raw_dir)
        self.aligner = TimeSeriesAligner(target_freq=self.cfg.data.sample_frequency)
        self.qc = SensorQualityChecker(config=self.cfg.sensor_quality)
        self.feature_engineer = FeatureEngineer(config=self.cfg.features)
        self.water_balance_analyzer = WaterBalanceAnalyzer()
        self.forecaster = BaselineFlowForecaster(config=self.cfg.models.baseline_forecaster)
        self.residual_detector = ResidualAnomalyDetector()
        self.stat_detector = StatisticalDetector(config=self.cfg.models.statistical_detector)
        self.iso_forest = WaterIsolationForest(config=self.cfg.models.isolation_forest)
        self.arbiter = EnsembleAnomalyArbiter(persistence_steps=self.cfg.models.statistical_detector.persistence_steps)
        self.evaluator = WaterLossEvaluator(detection_window_hours=self.cfg.evaluation.detection_window_hours)
        self.comparator = BenchmarkComparator(evaluator=self.evaluator)

    def run(self, save_artifacts: bool = True) -> Dict[str, Any]:
        """Runs the entire pipeline end-to-end.
        
        Args:
            save_artifacts: Whether to serialize processed datasets and report tables.
            
        Returns:
            Dictionary containing evaluation metrics, water balance audit, and detected event counts.
        """
        logger.info("==================================================")
        logger.info("   STARTING WATERPRINT ANALYTICS PIPELINE        ")
        logger.info("==================================================")
        
        # 1. Ingestion
        df_flow = self.data_loader.load_flow_records()
        df_pressure = self.data_loader.load_pressure_records()
        df_consumption = self.data_loader.load_consumption_records()
        df_leaks = self.data_loader.load_leak_ground_truth()
        topology = self.data_loader.load_topology()
        
        # 2. Alignment & Synchronization
        aligned_df = self.aligner.align_and_merge(df_flow, df_pressure, df_consumption)
        
        # 3. Sensor Quality Filtering
        cleaned_df, fault_log, quality_summary = self.qc.evaluate_quality(aligned_df)
        
        # 4. Feature Engineering
        features_df = self.feature_engineer.transform(cleaned_df)
        
        # 5. Water Balance & Minimum Night Flow
        water_audit = self.water_balance_analyzer.compute_macro_water_balance(features_df)
        daily_mnf_df = self.water_balance_analyzer.compute_minimum_night_flow_timeseries(features_df)
        
        # 6. Chronological Train / Test Split
        split_ratio = self.cfg.evaluation.train_split_ratio
        split_idx = int(split_ratio * len(features_df))
        train_df = features_df.iloc[:split_idx].copy()
        test_df = features_df.iloc[split_idx:].copy()
        test_start_time = test_df["timestamp"].min()
        test_end_time = test_df["timestamp"].max()
        logger.info(f"Chronological Split: Train ({len(train_df)} steps) | Test ({len(test_df)} steps)")
        
        # 7. Model Training & Baseline Forecasting
        self.forecaster.fit(train_df, target_col="flow_rate")
        
        # Predict on both train (for residual baseline) and test
        exp_train, low_train, upp_train = self.forecaster.predict(train_df)
        train_df["expected_flow"] = exp_train
        train_df["expected_lower_95"] = low_train
        train_df["expected_upper_95"] = upp_train
        train_res_df = self.residual_detector.analyze_residuals(train_df)
        
        exp_test, low_test, upp_test = self.forecaster.predict(test_df)
        test_df["expected_flow"] = exp_test
        test_df["expected_lower_95"] = low_test
        test_df["expected_upper_95"] = upp_test
        test_res_df = self.residual_detector.analyze_residuals(test_df)
        
        # 8. Statistical & CUSUM Change-Point Detection on Test
        z_scores, _ = self.stat_detector.detect_rolling_zscore(test_res_df["flow_residual"])
        cusum_stat, cusum_alarms = self.stat_detector.detect_cusum_changepoint(test_res_df["residual_zscore"])
        
        # 9. Isolation Forest
        self.iso_forest.fit(train_res_df)
        iso_scores, iso_alarms = self.iso_forest.predict(test_res_df)
        
        # 10. Multi-Tier Ensemble Event Arbiter
        scored_test_df, events_df = self.arbiter.evaluate_ensemble(
            test_res_df, cusum_alarms, iso_alarms, iso_scores
        )
        
        # 11. Network Topology & Event Localisation
        net_graph = NetworkGraph(topology)
        localiser = NetworkLocaliser(net_graph, config=self.cfg.localisation)
        
        enriched_events = []
        for idx, event in events_df.iterrows():
            e_dict = event.to_dict()
            t_start = pd.to_datetime(event["start_time"])
            t_end = pd.to_datetime(event["end_time"])
            
            # Slice test_res_df during this event
            evt_slice = test_res_df[(test_res_df["timestamp"] >= t_start) & (test_res_df["timestamp"] <= t_end)]
            loc_result = localiser.localise_event(evt_slice, baseline_df=train_df, top_k=self.cfg.localisation.top_k_candidates)
            
            e_dict["primary_candidate_zone"] = loc_result.get("primary_zone", "UNSPECIFIED")
            e_dict["candidate_zones"] = loc_result.get("candidate_zones", [])
            e_dict["candidate_nodes"] = loc_result.get("candidate_nodes", [])
            e_dict["localisation_summary"] = loc_result.get("supporting_rationale", "")
            enriched_events.append(e_dict)
            
        enriched_events_df = pd.DataFrame(enriched_events) if enriched_events else events_df
        
        # 12. Evaluation against Ground Truth Leaks
        eval_metrics = self.evaluator.evaluate_detections(
            enriched_events_df, df_leaks, test_start_time, test_end_time
        )
        
        # 13. Comparative Benchmarking against Baselines
        benchmark_table = self.comparator.run_benchmark_comparison(
            train_df, test_df, enriched_events_df, df_leaks
        )
        
        # 14. Artifact Serialization
        if save_artifacts:
            os.makedirs(self.cfg.data.processed_dir, exist_ok=True)
            os.makedirs("reports", exist_ok=True)
            
            # Combine train and test into full processed dataset
            full_processed = pd.concat([train_res_df, scored_test_df], axis=0).reset_index(drop=True)
            full_processed_path = os.path.join(self.cfg.data.processed_dir, "processed_network_timeseries.parquet")
            full_processed.to_parquet(full_processed_path, index=False)
            
            # Save CSV copy for convenience
            full_processed_csv = os.path.join(self.cfg.data.processed_dir, "processed_network_timeseries.csv")
            full_processed.to_csv(full_processed_csv, index=False)
            
            # Fault log
            fault_log_path = os.path.join(self.cfg.data.processed_dir, "sensor_fault_registry.csv")
            fault_log.to_csv(fault_log_path, index=False)
            
            # Daily MNF
            mnf_path = os.path.join(self.cfg.data.processed_dir, "daily_minimum_night_flow.csv")
            daily_mnf_df.to_csv(mnf_path, index=False)
            
            # Events
            events_csv = "reports/anomaly_events.csv"
            # Format candidate columns to JSON string for clean CSV export
            events_export = enriched_events_df.copy()
            if "candidate_zones" in events_export.columns:
                events_export["candidate_zones"] = events_export["candidate_zones"].apply(json.dumps)
            if "candidate_nodes" in events_export.columns:
                events_export["candidate_nodes"] = events_export["candidate_nodes"].apply(json.dumps)
            events_export.to_csv(events_csv, index=False)
            
            # Benchmark Comparison
            benchmark_csv = "reports/benchmark_comparison.csv"
            benchmark_table.to_csv(benchmark_csv, index=False)
            
            # Summary JSON
            summary = {
                "evaluation_metrics": eval_metrics,
                "water_balance_audit": water_audit,
                "sensor_quality_summary": quality_summary,
                "total_events_detected": len(enriched_events_df),
                "benchmark_comparison": benchmark_table.to_dict(orient="records")
            }
            summary_json_path = "reports/evaluation_summary.json"
            with open(summary_json_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
                
            logger.info("All pipeline artifacts successfully exported to data/processed/ and reports/")

        logger.info("==================================================")
        logger.info("   PIPELINE EXECUTION COMPLETED SUCCESSFULLY      ")
        logger.info("==================================================")
        
        return {
            "eval_metrics": eval_metrics,
            "water_audit": water_audit,
            "quality_summary": quality_summary,
            "events_count": len(enriched_events_df),
            "benchmark_table": benchmark_table
        }

if __name__ == "__main__":
    pipeline = WaterprintPipeline()
    pipeline.run(save_artifacts=True)
