"""Hydraulic Sensitivity & Candidate Zone Localisation Module for WATERPRINT.

Localizes pipe leaks by comparing observed nodal pressure residual drops
against theoretical hydraulic sensitivity profiles across the NetworkX graph.
Outputs ranked candidate zones and nodes with explicit uncertainty bounds.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
from src.localisation.network_graph import NetworkGraph
from src.utils.logging import logger
from src.utils.config import LocalisationConfig

class NetworkLocaliser:
    """Ranks candidate network zones and nodes based on pressure residual fingerprints."""
    
    def __init__(self, network_graph: NetworkGraph, config: Optional[LocalisationConfig] = None):
        self.net = network_graph
        self.cfg = config or LocalisationConfig()
        self.sensor_nodes = self.net.sensor_nodes
        self._precompute_sensitivity_matrix()
        
    def _precompute_sensitivity_matrix(self):
        """Constructs theoretical pressure drop sensitivity profiles S for all network nodes."""
        all_nodes = [n for n in self.net.graph.nodes() if n != "RES_1"]
        self.candidate_nodes = sorted(all_nodes)
        
        # Matrix S of shape (n_sensors, n_candidates)
        m = len(self.sensor_nodes)
        n = len(self.candidate_nodes)
        self.sensitivity_matrix = np.zeros((m, n))
        
        gamma = self.cfg.hydraulic_resistance_decay
        for col_idx, cand in enumerate(self.candidate_nodes):
            for row_idx, sn in enumerate(self.sensor_nodes):
                if cand == sn:
                    # Sensor is at the leak node -> maximum sensitivity
                    self.sensitivity_matrix[row_idx, col_idx] = 1.0
                else:
                    dist = self.net.get_shortest_hydraulic_distance(cand, sn)
                    # Decay sensitivity inversely with normalized hydraulic distance
                    norm_dist = min(50.0, dist / 100.0)
                    self.sensitivity_matrix[row_idx, col_idx] = np.exp(-gamma * norm_dist)
                    
        # Normalize each column to unit vector
        col_norms = np.linalg.norm(self.sensitivity_matrix, axis=0, keepdims=True)
        col_norms[col_norms == 0.0] = 1.0
        self.normalized_S = self.sensitivity_matrix / col_norms

    def localise_event(
        self,
        event_df: pd.DataFrame,
        baseline_df: Optional[pd.DataFrame] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """Localizes a specific anomaly event slice by analyzing its pressure drop signature.
        
        Args:
            event_df: Time-series slice of the network during the confirmed leak event.
            baseline_df: Clean baseline slice used for calculating reference pressure.
            top_k: Number of candidate zones/nodes to return.
            
        Returns:
            Dictionary containing ranked candidate zones, ranked candidate nodes,
            observed pressure drops per sensor, and supporting hydraulic rationale.
        """
        # Calculate mean observed pressure head at each sensor during event
        sensor_drops = {}
        r_p = []
        
        for sn in self.sensor_nodes:
            col_name = f"pressure_{sn}"
            if col_name in event_df.columns:
                obs_head = float(event_df[col_name].mean())
                # Baseline reference head
                if baseline_df is not None and col_name in baseline_df.columns:
                    ref_head = float(baseline_df[col_name].mean())
                else:
                    # Estimate baseline via 90th percentile during normal periods
                    ref_head = float(event_df[col_name].quantile(0.85))
                    
                drop = max(0.0, ref_head - obs_head)
                sensor_drops[sn] = round(drop, 2)
                r_p.append(drop)
            else:
                sensor_drops[sn] = 0.0
                r_p.append(0.0)
                
        r_p = np.array(r_p)
        r_norm = np.linalg.norm(r_p)
        
        # If all pressure drops are near zero, we cannot localise with high confidence
        if r_norm < 0.15:
            return {
                "localisation_status": "AMBIGUOUS",
                "message": "Pressure drops across all sensors are below detection threshold (< 0.15m). Leak volume too small for spatial resolution.",
                "candidate_zones": [{"zone": "UNSPECIFIED", "probability_pct": 100.0}],
                "candidate_nodes": [],
                "sensor_drops": sensor_drops
            }
            
        r_p_normed = r_p / r_norm
        
        # Calculate Cosine similarity and Correlation against every candidate node column
        similarities = np.dot(r_p_normed, self.normalized_S)
        # Clip to positive
        similarities = np.maximum(0.0, similarities)
        
        # Softmax / probability distribution with temperature scaling
        temperature = 0.25
        exp_sim = np.exp(similarities / temperature)
        node_probs = exp_sim / np.sum(exp_sim)
        
        # Rank Nodes
        ranked_node_indices = np.argsort(node_probs)[::-1]
        top_nodes = []
        for rank, idx in enumerate(ranked_node_indices[:top_k * 2], 1):
            nid = self.candidate_nodes[idx]
            top_nodes.append({
                "rank": rank,
                "node_id": nid,
                "zone": self.net.node_zones.get(nid, "UNKNOWN"),
                "probability_pct": round(float(node_probs[idx]) * 100.0, 1),
                "coordinates": self.net.node_coords.get(nid, (0, 0))
            })
            
        # Aggregate Probabilities by Zone
        zone_probs: Dict[str, float] = {}
        for idx, nid in enumerate(self.candidate_nodes):
            z = self.net.node_zones.get(nid, "UNKNOWN")
            zone_probs[z] = zone_probs.get(z, 0.0) + float(node_probs[idx])
            
        # Sort Zones
        sorted_zones = sorted(zone_probs.items(), key=lambda x: x[1], reverse=True)
        top_zones = [
            {"zone": z, "probability_pct": round(p * 100.0, 1)}
            for z, p in sorted_zones[:top_k]
        ]
        
        # Primary sensor exhibiting maximum drop
        max_sensor = max(sensor_drops.items(), key=lambda x: x[1])
        rationale = (
            f"Maximum localized hydraulic head loss of {max_sensor[1]:.2f}m detected at sensor '{max_sensor[0]}'. "
            f"Top candidate zone is '{top_zones[0]['zone']}' with {top_zones[0]['probability_pct']}% confidence. "
            f"Primary candidate nodes: {', '.join([n['node_id'] for n in top_nodes[:3]])}."
        )
        
        return {
            "localisation_status": "RESOLVED",
            "primary_zone": top_zones[0]["zone"],
            "primary_zone_confidence_pct": top_zones[0]["probability_pct"],
            "candidate_zones": top_zones,
            "candidate_nodes": top_nodes[:top_k],
            "max_drop_sensor": max_sensor[0],
            "max_drop_head_m": max_sensor[1],
            "sensor_drops": sensor_drops,
            "supporting_rationale": rationale
        }
