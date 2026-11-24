"""Network Topological Graph Representation for WATERPRINT.

Encapsulates the water distribution network as a weighted NetworkX graph,
calculating hydraulic resistance weights, shortest paths, and zone partitioning.
"""

from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
import numpy as np
from src.utils.logging import logger
from src.utils.exceptions import TopologyError

class NetworkGraph:
    """Manages hydraulic topological graph structures using NetworkX."""
    
    def __init__(self, topology_dict: Dict[str, Any]):
        self.topology = topology_dict
        self.graph = nx.Graph()
        self.sensor_nodes: List[str] = []
        self.node_zones: Dict[str, str] = {}
        self.node_coords: Dict[str, Tuple[float, float]] = {}
        self._build_graph()
        
    def _build_graph(self):
        """Constructs nodes and weighted edges from topology dictionary."""
        if "nodes" not in self.topology or "pipes" not in self.topology:
            raise TopologyError("Invalid topology schema: 'nodes' and 'pipes' required.")
            
        # Add Nodes
        for n in self.topology["nodes"]:
            nid = n["node_id"]
            zone = n.get("zone", "DEFAULT")
            has_sensor = n.get("has_pressure_sensor", False)
            coords = n.get("coordinates", {})
            x = coords.get("x", 0.0)
            y = coords.get("y", 0.0)
            
            self.graph.add_node(
                nid,
                elevation=n.get("elevation", 0.0),
                base_demand=n.get("base_demand", 0.0),
                zone=zone,
                has_sensor=has_sensor,
                x=x,
                y=y
            )
            self.node_zones[nid] = zone
            self.node_coords[nid] = (x, y)
            if has_sensor:
                self.sensor_nodes.append(nid)
                
        # Add Pipes / Edges
        for p in self.topology["pipes"]:
            u = p["start_node"]
            v = p["end_node"]
            length = float(p.get("length", 100.0))
            diam_mm = float(p.get("diameter", 150.0))
            roughness = float(p.get("roughness", 110.0))
            
            # Hazen-Williams hydraulic resistance factor:
            # Resistance R is proportional to L / (C^1.852 * D^4.87)
            diam_m = diam_mm / 1000.0
            r_weight = (10.67 * length) / (max(1.0, roughness ** 1.852) * max(1e-4, diam_m ** 4.87))
            
            self.graph.add_edge(
                u, v,
                pipe_id=p.get("pipe_id", f"p_{u}_{v}"),
                length=length,
                diameter=diam_mm,
                roughness=roughness,
                material=p.get("material", "Unknown"),
                hydraulic_weight=float(r_weight)
            )
            
        logger.info(f"Built NetworkGraph with {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} pipes, and {len(self.sensor_nodes)} pressure sensors.")

    def get_shortest_hydraulic_distance(self, source: str, target: str) -> float:
        """Computes shortest hydraulic resistance distance between two nodes."""
        try:
            return nx.shortest_path_length(self.graph, source=source, target=target, weight="hydraulic_weight")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return 1e6

    def get_zone_distribution(self) -> Dict[str, List[str]]:
        """Returns mapping of zone name to list of contained junction node IDs."""
        zones: Dict[str, List[str]] = {}
        for nid, z in self.node_zones.items():
            zones.setdefault(z, []).append(nid)
        return zones
