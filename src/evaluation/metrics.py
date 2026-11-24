"""Evaluation Metrics Module for WATERPRINT.

Calculates event-based Precision, Recall, F1-Score, Detection Delay,
False Alarm Rate (FAR), and Localisation Accuracy against ground-truth benchmarks.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from src.utils.logging import logger

class WaterLossEvaluator:
    """Computes operational leak detection metrics on chronological evaluation windows."""
    
    def __init__(self, detection_window_hours: float = 24.0):
        self.detection_window_hours = detection_window_hours
        
    def evaluate_detections(
        self,
        detected_events_df: pd.DataFrame,
        ground_truth_df: pd.DataFrame,
        test_start_time: pd.Timestamp,
        test_end_time: pd.Timestamp
    ) -> Dict[str, Any]:
        """Evaluates detected events against ground truth leak records.
        
        Args:
            detected_events_df: DataFrame of detected leak events.
            ground_truth_df: DataFrame of true known leak events.
            test_start_time: Start timestamp of the evaluation period.
            test_end_time: End timestamp of the evaluation period.
            
        Returns:
            Dictionary containing Precision, Recall, F1, Detection Delay, FAR, and Localisation accuracy.
        """
        logger.info("Evaluating detection performance against ground truth benchmarks...")
        
        # Test duration in months (30 days / month)
        test_duration_days = max(1.0, (test_end_time - test_start_time).total_seconds() / 86400.0)
        test_duration_months = test_duration_days / 30.0
        
        # Filter ground truth leaks that fall within the test period
        gt = ground_truth_df.copy()
        if not gt.empty:
            if not pd.api.types.is_datetime64_any_dtype(gt["start_time"]):
                gt["start_time"] = pd.to_datetime(gt["start_time"])
            if not pd.api.types.is_datetime64_any_dtype(gt["end_time"]):
                gt["end_time"] = pd.to_datetime(gt["end_time"])
            gt = gt[(gt["end_time"] >= test_start_time) & (gt["start_time"] <= test_end_time)].reset_index(drop=True)
            
        n_ground_truth = len(gt)
        
        det = detected_events_df.copy()
        if not det.empty:
            if not pd.api.types.is_datetime64_any_dtype(det["start_time"]):
                det["start_time"] = pd.to_datetime(det["start_time"])
            if not pd.api.types.is_datetime64_any_dtype(det["end_time"]):
                det["end_time"] = pd.to_datetime(det["end_time"])
            det = det[(det["end_time"] >= test_start_time) & (det["start_time"] <= test_end_time)].reset_index(drop=True)
            
        n_detected = len(det)
        
        if n_ground_truth == 0:
            logger.warning("No ground truth leaks in evaluation window. Recall cannot be evaluated.")
            return {
                "total_ground_truth_leaks": 0,
                "total_detected_events": n_detected,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "mean_detection_delay_hours": 0.0,
                "false_alarms_per_month": round(n_detected / test_duration_months, 2)
            }
            
        # Match detected events to ground truth leaks
        tp_count = 0
        delays_hours = []
        matched_gt_indices = set()
        matched_det_indices = set()
        localisation_top1_hits = 0
        localisation_top3_hits = 0
        
        for gt_idx, gt_row in gt.iterrows():
            gt_start = gt_row["start_time"]
            gt_end = gt_row["end_time"]
            target_node = str(gt_row.get("target_node_id", ""))
            
            # Find any detected events that overlap with this leak window
            # (with a tolerance of up to detection_window_hours before end)
            overlaps = []
            for det_idx, det_row in det.iterrows():
                d_start = det_row["start_time"]
                d_end = det_row["end_time"]
                
                # Overlap check
                if not (d_end < gt_start or d_start > gt_end):
                    overlaps.append((det_idx, d_start, det_row))
                    
            if overlaps:
                tp_count += 1
                matched_gt_indices.add(gt_idx)
                
                # First detection delay
                earliest_det = min(overlaps, key=lambda x: x[1])
                matched_det_indices.add(earliest_det[0])
                delay_sec = max(0.0, (earliest_det[1] - gt_start).total_seconds())
                delay_hrs = delay_sec / 3600.0
                delays_hours.append(delay_hrs)
                
                # Check localisation accuracy if candidate information exists
                det_record = earliest_det[2]
                cand_nodes = det_record.get("candidate_nodes", [])
                if isinstance(cand_nodes, list) and cand_nodes:
                    node_ids = [n.get("node_id") for n in cand_nodes if isinstance(n, dict)]
                    if node_ids and node_ids[0] == target_node:
                        localisation_top1_hits += 1
                    if target_node in node_ids[:3]:
                        localisation_top3_hits += 1
                        
        fp_count = n_detected - len(matched_det_indices)
        fn_count = n_ground_truth - tp_count
        
        precision = tp_count / max(1, (tp_count + fp_count))
        recall = tp_count / max(1, (tp_count + fn_count))
        f1 = (2 * precision * recall) / max(1e-4, (precision + recall))
        mean_delay = float(np.mean(delays_hours)) if delays_hours else 0.0
        far = fp_count / test_duration_months
        
        top1_acc = (localisation_top1_hits / max(1, tp_count)) * 100.0
        top3_acc = (localisation_top3_hits / max(1, tp_count)) * 100.0
        
        results = {
            "test_duration_days": round(test_duration_days, 1),
            "test_duration_months": round(test_duration_months, 2),
            "total_ground_truth_leaks": n_ground_truth,
            "true_positive_leaks_detected": tp_count,
            "false_negative_missed_leaks": fn_count,
            "false_positive_alarms": fp_count,
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1_score": round(f1, 3),
            "mean_detection_delay_hours": round(mean_delay, 2),
            "false_alarms_per_month": round(far, 2),
            "localisation_top1_accuracy_pct": round(top1_acc, 1),
            "localisation_top3_accuracy_pct": round(top3_acc, 1)
        }
        
        logger.info(
            f"Evaluation Results -> Precision: {results['precision']:.3f}, "
            f"Recall: {results['recall']:.3f}, F1: {results['f1_score']:.3f}, "
            f"Mean Delay: {results['mean_detection_delay_hours']}h, FAR: {results['false_alarms_per_month']}/mo"
        )
        return results
