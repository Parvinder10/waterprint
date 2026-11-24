import React, { useState } from 'react';
import { Map, Layers, Radio, Info } from 'lucide-react';

export default function TopologyMap({ topology, candidateNodes = [] }) {
  const [selectedZone, setSelectedZone] = useState('ALL');
  const [hoverNode, setHoverNode] = useState(null);

  if (!topology || !topology.nodes) return null;

  const nodes = topology.nodes || [];
  const pipes = topology.pipes || [];

  // Calculate coordinate bounding box for SVG projection
  const xs = nodes.map(n => n.coordinates?.x || 0);
  const ys = nodes.map(n => n.coordinates?.y || 0);
  const minX = Math.min(...xs);
  const maxX = Math.max(...xs);
  const minY = Math.min(...ys);
  const maxY = Math.max(...ys);

  const svgWidth = 900;
  const svgHeight = 440;
  const pad = 40;

  const projectX = (x) => pad + ((x - minX) / Math.max(1, maxX - minX)) * (svgWidth - pad * 2);
  const projectY = (y) => svgHeight - pad - ((y - minY) / Math.max(1, maxY - minY)) * (svgHeight - pad * 2);

  const nodeMap = {};
  nodes.forEach(n => {
    nodeMap[n.node_id] = {
      ...n,
      px: projectX(n.coordinates?.x || 0),
      py: projectY(n.coordinates?.y || 0)
    };
  });

  const zoneColors = {
    'ZONE_NORTH_WEST': '#3b82f6',
    'ZONE_NORTH_EAST': '#8b5cf6',
    'ZONE_CENTRAL': '#10b981',
    'ZONE_COMMERCIAL': '#f59e0b',
    'SOURCE': '#ef4444'
  };

  const candidateSet = new Set(candidateNodes.map(n => typeof n === 'string' ? n : n.node_id));

  return (
    <div className="glass-panel" style={{ marginBottom: '24px' }}>
      <div className="flex items-center justify-between flex-wrap gap-4" style={{ marginBottom: '16px' }}>
        <div>
          <div className="flex items-center gap-2">
            <Map size={20} color="#38bdf8" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              Network Topology Map (L-Town DMA_NORTH)
            </h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Physical pipe connections, piezoresistive pressure transducers, and topological zone partitioning.
          </p>
        </div>

        {/* Zone Filters */}
        <div className="flex items-center gap-2 flex-wrap">
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>FILTER:</span>
          {['ALL', 'ZONE_NORTH_EAST', 'ZONE_NORTH_WEST', 'ZONE_CENTRAL', 'ZONE_COMMERCIAL'].map(z => (
            <button
              key={z}
              onClick={() => setSelectedZone(z)}
              className={`tab-btn ${selectedZone === z ? 'active' : ''}`}
              style={{ padding: '4px 10px', fontSize: '0.7rem' }}
            >
              {z.replace('ZONE_', '')}
            </button>
          ))}
        </div>
      </div>

      {/* SVG Canvas */}
      <div style={{ width: '100%', background: '#020617', borderRadius: '8px', border: '1px solid var(--border-color)', position: 'relative', overflow: 'hidden' }}>
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          style={{ width: '100%', height: 'auto', display: 'block' }}
        >
          {/* Pipes (Lines) */}
          {pipes.map((p, idx) => {
            const u = nodeMap[p.start_node];
            const v = nodeMap[p.end_node];
            if (!u || !v) return null;

            const isDimmed = selectedZone !== 'ALL' && (u.zone !== selectedZone && v.zone !== selectedZone);
            const strokeColor = isDimmed ? 'rgba(51, 65, 85, 0.2)' : 'rgba(100, 116, 139, 0.6)';
            const strokeW = Math.max(1.5, (p.diameter || 150) / 80);

            return (
              <line
                key={`pipe-${idx}`}
                x1={u.px}
                y1={u.py}
                x2={v.px}
                y2={v.py}
                stroke={strokeColor}
                strokeWidth={strokeW}
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((n) => {
            const pos = nodeMap[n.node_id];
            if (!pos) return null;

            const isDimmed = selectedZone !== 'ALL' && n.zone !== selectedZone;
            const isCandidate = candidateSet.has(n.node_id);
            const isSensor = n.has_pressure_sensor;
            const color = zoneColors[n.zone] || '#64748b';

            return (
              <g
                key={n.node_id}
                onMouseEnter={() => setHoverNode(n)}
                onMouseLeave={() => setHoverNode(null)}
                style={{ cursor: 'pointer', opacity: isDimmed ? 0.25 : 1 }}
              >
                {/* Candidate Highlight Glow */}
                {isCandidate && (
                  <circle
                    cx={pos.px}
                    cy={pos.py}
                    r="16"
                    fill="none"
                    stroke="#f43f5e"
                    strokeWidth="2.5"
                    strokeDasharray="3 3"
                  >
                    <animate attributeName="r" values="12;20;12" dur="2s" repeatCount="indefinite" />
                    <animate attributeName="opacity" values="0.8;0.2;0.8" dur="2s" repeatCount="indefinite" />
                  </circle>
                )}

                {/* Node Shape: Diamond for Pressure Sensor, Circle for Junction */}
                {isSensor ? (
                  <rect
                    x={pos.px - 6}
                    y={pos.py - 6}
                    width="12"
                    height="12"
                    transform={`rotate(45 ${pos.px} ${pos.py})`}
                    fill={color}
                    stroke="#ffffff"
                    strokeWidth="1.5"
                  />
                ) : (
                  <circle
                    cx={pos.px}
                    cy={pos.py}
                    r={n.node_id === 'RES_1' ? 9 : 5}
                    fill={color}
                    stroke="#0f172a"
                    strokeWidth="1.5"
                  />
                )}

                {/* Label for sensors and reservoirs */}
                {(isSensor || n.node_id === 'RES_1') && (
                  <text
                    x={pos.px}
                    y={pos.py - 10}
                    fill="#f8fafc"
                    fontSize="10"
                    fontWeight="700"
                    textAnchor="middle"
                    fontFamily="var(--font-mono)"
                  >
                    {n.node_id}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {/* Hover Tooltip Overlay */}
        {hoverNode && (
          <div style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            borderRadius: '8px',
            padding: '12px 16px',
            fontSize: '0.8rem',
            backdropFilter: 'blur(8px)',
            pointerEvents: 'none',
            maxWidth: '280px'
          }}>
            <div className="flex items-center justify-between" style={{ marginBottom: '6px' }}>
              <span style={{ fontWeight: 800, color: '#38bdf8' }}>{hoverNode.node_id}</span>
              <span className="badge badge-medium" style={{ fontSize: '0.65rem' }}>{hoverNode.zone}</span>
            </div>
            <div>Elevation: <span style={{ color: '#f8fafc', fontWeight: 600 }}>{hoverNode.elevation}m</span></div>
            <div>Base Demand: <span style={{ color: '#f8fafc', fontWeight: 600 }}>{hoverNode.base_demand} m³/h</span></div>
            <div>Sensor: <span style={{ color: hoverNode.has_pressure_sensor ? '#34d399' : 'var(--text-muted)', fontWeight: 600 }}>
              {hoverNode.has_pressure_sensor ? 'Active Pressure Transducer' : 'None'}
            </span></div>
          </div>
        )}
      </div>

      {/* Map Legend */}
      <div className="flex items-center justify-between flex-wrap gap-4" style={{ marginTop: '16px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-4 flex-wrap">
          {Object.entries(zoneColors).map(([zone, color]) => (
            <div key={zone} className="flex items-center gap-2">
              <span style={{ width: '10px', height: '10px', background: color, borderRadius: '50%', display: 'inline-block' }}></span>
              <span>{zone.replace('ZONE_', '')}</span>
            </div>
          ))}
          <div className="flex items-center gap-2">
            <span style={{ width: '10px', height: '10px', background: '#38bdf8', transform: 'rotate(45deg)', display: 'inline-block', border: '1px solid #ffffff' }}></span>
            <span>Pressure Transducer</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ width: '12px', height: '12px', border: '2px dashed #f43f5e', borderRadius: '50%', display: 'inline-block' }}></span>
            <span>Suspected Leak Area</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Info size={14} />
          <span>Coordinates from EPANET calibrated benchmark.</span>
        </div>
      </div>
    </div>
  );
}
