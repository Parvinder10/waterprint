"""Interactive Plotly Visualisation Components for the WATERPRINT Dashboard."""

from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_network_topology(
    topology: Dict[str, Any],
    candidate_nodes: Optional[List[str]] = None,
    candidate_zone: Optional[str] = None
) -> go.Figure:
    """Renders interactive 2D topological map with pipe connectivity, sensors, and candidate zones."""
    fig = go.Figure()
    
    # 1. Draw Pipes (Edges)
    node_dict = {n["node_id"]: n for n in topology["nodes"]}
    edge_x = []
    edge_y = []
    edge_hover = []
    
    for p in topology["pipes"]:
        u = p["start_node"]
        v = p["end_node"]
        if u in node_dict and v in node_dict:
            x0 = node_dict[u]["coordinates"]["x"]
            y0 = node_dict[u]["coordinates"]["y"]
            x1 = node_dict[v]["coordinates"]["x"]
            y1 = node_dict[v]["coordinates"]["y"]
            
            fig.add_trace(go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode="lines",
                line=dict(color="#94a3b8", width=max(1.5, p.get("diameter", 150.0) / 75.0)),
                hoverinfo="text",
                hovertext=f"Pipe: {p['pipe_id']}<br>Diam: {p.get('diameter')}mm<br>Length: {p.get('length')}m<br>Mat: {p.get('material')}",
                showlegend=False
            ))
            
    # 2. Draw Nodes
    zone_colors = {
        "ZONE_NORTH_WEST": "#3b82f6",
        "ZONE_NORTH_EAST": "#8b5cf6",
        "ZONE_CENTRAL": "#10b981",
        "ZONE_COMMERCIAL": "#f59e0b",
        "SOURCE": "#ef4444"
    }
    
    for zone in topology.get("zones", []) + ["SOURCE"]:
        zn_nodes = [n for n in topology["nodes"] if n.get("zone") == zone]
        if not zn_nodes:
            continue
            
        x_vals = [n["coordinates"]["x"] for n in zn_nodes]
        y_vals = [n["coordinates"]["y"] for n in zn_nodes]
        names = [n["node_id"] for n in zn_nodes]
        elevs = [n.get("elevation", 0.0) for n in zn_nodes]
        is_sensor = [n.get("has_pressure_sensor", False) for n in zn_nodes]
        
        # Determine symbol: diamond for sensors, circle for standard junctions
        symbols = ["diamond-wide" if s else "circle" for s in is_sensor]
        sizes = [15 if s else 9 for s in is_sensor]
        
        hover_texts = [
            f"Node: {nid}<br>Zone: {zone}<br>Elevation: {elev}m<br>Sensor: {'Active Pressure Transducer' if s else 'None'}"
            for nid, elev, s in zip(names, elevs, is_sensor)
        ]
        
        fig.add_trace(go.Scatter(
            x=x_vals,
            y=y_vals,
            mode="markers+text",
            text=[nid if s else "" for nid, s in zip(names, is_sensor)],
            textposition="top center",
            textfont=dict(size=10, color="#1e293b"),
            marker=dict(
                size=sizes,
                color=zone_colors.get(zone, "#64748b"),
                symbol=symbols,
                line=dict(width=1.5, color="#0f172a")
            ),
            name=zone,
            hoverinfo="text",
            hovertext=hover_texts
        ))
        
    # 3. Highlight Candidate Localisation Target if active
    if candidate_nodes:
        cand_x = [node_dict[n]["coordinates"]["x"] for n in candidate_nodes if n in node_dict]
        cand_y = [node_dict[n]["coordinates"]["y"] for n in candidate_nodes if n in node_dict]
        fig.add_trace(go.Scatter(
            x=cand_x,
            y=cand_y,
            mode="markers",
            marker=dict(size=24, color="rgba(239, 68, 68, 0.35)", symbol="circle", line=dict(color="#ef4444", width=3)),
            name="Suspected Leak Area",
            hoverinfo="text",
            hovertext=[f"Ranked Candidate Node: {n}" for n in candidate_nodes]
        ))
        
    fig.update_layout(
        title="<b>Water Distribution Network Topology (DMA_NORTH)</b>",
        xaxis=dict(title="Local Easting (m)", showgrid=True, gridcolor="#f1f5f9"),
        yaxis=dict(title="Local Northing (m)", showgrid=True, gridcolor="#f1f5f9", scaleanchor="x", scaleratio=1),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        height=520,
        margin=dict(l=30, r=30, t=50, b=50)
    )
    return fig

def plot_flow_expected_vs_observed(df: pd.DataFrame) -> go.Figure:
    """Renders interactive observed vs. expected flow with 95% Bayesian prediction interval."""
    fig = go.Figure()
    
    ts = df["timestamp"]
    
    # 95% Prediction Interval Band
    if "expected_upper_95" in df.columns and "expected_lower_95" in df.columns:
        fig.add_trace(go.Scatter(
            x=ts, y=df["expected_upper_95"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip"
        ))
        fig.add_trace(go.Scatter(
            x=ts, y=df["expected_lower_95"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(59, 130, 246, 0.15)",
            name="95% Forecast Interval",
            hoverinfo="skip"
        ))
        
    # Expected Baseline
    if "expected_flow" in df.columns:
        fig.add_trace(go.Scatter(
            x=ts, y=df["expected_flow"],
            mode="lines",
            line=dict(color="#2563eb", width=2, dash="dash"),
            name="Expected Baseline Flow (m³/h)"
        ))
        
    # Observed Inflow
    fig.add_trace(go.Scatter(
        x=ts, y=df["flow_rate"],
        mode="lines",
        line=dict(color="#0f172a", width=1.8),
        name="Observed Inflow (m³/h)"
    ))
    
    # Highlight Confirmed Leak Alarms
    if "leak_alarm_active" in df.columns:
        leak_mask = df["leak_alarm_active"] == True
        if leak_mask.any():
            fig.add_trace(go.Scatter(
                x=df.loc[leak_mask, "timestamp"],
                y=df.loc[leak_mask, "flow_rate"],
                mode="markers",
                marker=dict(color="#dc2626", size=6, symbol="x"),
                name="Leak Anomaly Triggered"
            ))
            
    fig.update_layout(
        title="<b>DMA Inlet Flow: Observed vs. Forecasted Baseline with 95% Confidence Bounds</b>",
        xaxis=dict(title="Timestamp", rangeslider=dict(visible=True)),
        yaxis=dict(title="Flow Rate (m³/h)"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return fig

def plot_residual_and_pressure(df: pd.DataFrame) -> go.Figure:
    """Renders dual subplots for flow residual discrepancy and network pressure response."""
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.10,
        subplot_titles=("<b>Volumetric Flow Residual [Q_obs - Q_expected] (m³/h)</b>", "<b>Network Average Pressure Head (m)</b>")
    )
    
    ts = df["timestamp"]
    
    # Residual Flow
    res = df.get("flow_residual", df["flow_rate"] - df.get("expected_flow", df["flow_rate"]))
    fig.add_trace(go.Scatter(
        x=ts, y=res,
        mode="lines",
        line=dict(color="#ea580c", width=1.5),
        name="Flow Residual (m³/h)"
    ), row=1, col=1)
    
    fig.add_hline(y=0.0, line_dash="dash", line_color="#94a3b8", row=1, col=1)
    
    # Pressure Head
    p_cols = [c for c in df.columns if c.startswith("pressure_n")]
    if p_cols:
        for p_col in p_cols[:4]: # Plot top 4 sensors for legibility
            fig.add_trace(go.Scatter(
                x=ts, y=df[p_col],
                mode="lines",
                line=dict(width=1.2),
                name=f"Pressure Head {p_col.replace('pressure_', '')} (m)"
            ), row=2, col=1)
    elif "pressure_mean" in df.columns:
        fig.add_trace(go.Scatter(
            x=ts, y=df["pressure_mean"],
            mode="lines",
            line=dict(color="#0284c7", width=1.5),
            name="Mean Pressure (m)"
        ), row=2, col=1)
        
    fig.update_layout(
        template="plotly_white",
        height=520,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return fig

def plot_daily_mnf(daily_mnf_df: pd.DataFrame) -> go.Figure:
    """Renders daily Minimum Night Flow (MNF) and Net Night Flow (NNF) loss progression."""
    fig = go.Figure()
    
    dates = daily_mnf_df["date"]
    
    # MNF Total Flow
    fig.add_trace(go.Scatter(
        x=dates, y=daily_mnf_df["mnf_flow_mean"],
        mode="lines+markers",
        line=dict(color="#0284c7", width=2),
        name="Minimum Night Flow (02:00-04:00 AM)"
    ))
    
    # Net Night Flow
    fig.add_trace(go.Scatter(
        x=dates, y=daily_mnf_df["net_night_flow_nnf"],
        mode="lines+markers",
        line=dict(color="#d97706", width=2),
        name="Net Night Flow (NNF)"
    ))
    
    # Unexplained Night Loss
    fig.add_trace(go.Bar(
        x=dates, y=daily_mnf_df["unexplained_night_loss"],
        marker_color="rgba(220, 38, 38, 0.65)",
        name="Unexplained Nocturnal Loss (m³/h)"
    ))
    
    # Legitimate Night Demand Baseline
    fig.add_trace(go.Scatter(
        x=dates, y=daily_mnf_df["legitimate_night_demand"],
        mode="lines",
        line=dict(color="#10b981", dash="dot", width=1.5),
        name="Authorized Night Baseline"
    ))
    
    fig.update_layout(
        title="<b>Diurnal Minimum Night Flow (MNF) and Unexplained Nocturnal Loss Tracking</b>",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Flow Rate (m³/h)"),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=420,
        margin=dict(l=40, r=20, t=60, b=40)
    )
    return fig
