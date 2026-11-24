import React, { useState, useMemo } from 'react';
import { Activity, Clock, Eye, Sliders } from 'lucide-react';

export default function FlowPressureChart({ timeseriesData }) {
  const [zoomRange, setZoomRange] = useState('7d'); // '24h', '3d', '7d', 'all'
  const [hoverIndex, setHoverIndex] = useState(null);

  const series = timeseriesData?.timeseries || [];

  // Filter series based on zoom range
  const filteredData = useMemo(() => {
    if (!series.length) return [];
    const count = series.length;
    let sliceLen = count;
    if (zoomRange === '24h') sliceLen = Math.min(count, 96);
    else if (zoomRange === '3d') sliceLen = Math.min(count, 96 * 3);
    else if (zoomRange === '7d') sliceLen = Math.min(count, 96 * 7);
    return series.slice(0, sliceLen);
  }, [series, zoomRange]);

  if (!filteredData.length) {
    return (
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <p style={{ color: 'var(--text-muted)' }}>No time-series data available for the selected range.</p>
      </div>
    );
  }

  // Calculate SVG bounds
  const width = 1000;
  const heightFlow = 260;
  const heightPressure = 120;
  const padLeft = 60;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 30;

  const chartW = width - padLeft - padRight;

  // Max and min flow
  const flows = filteredData.map(d => d.flow_rate || 0);
  const uppers = filteredData.map(d => d.expected_upper_95 || d.flow_rate || 0);
  const lowers = filteredData.map(d => d.expected_lower_95 || d.flow_rate || 0);
  const maxFlow = Math.max(...flows, ...uppers) * 1.1;
  const minFlow = Math.max(0, Math.min(...flows, ...lowers) * 0.9);

  // Pressure bounds
  const pressures = filteredData.map(d => d.pressure_mean || 45);
  const maxP = Math.max(...pressures) * 1.05;
  const minP = Math.min(...pressures) * 0.95;

  const getX = (idx) => padLeft + (idx / Math.max(1, filteredData.length - 1)) * chartW;
  const getYFlow = (val) => padTop + (1 - (val - minFlow) / Math.max(1, maxFlow - minFlow)) * heightFlow;
  const getYPress = (val) => 15 + (1 - (val - minP) / Math.max(1, maxP - minP)) * (heightPressure - 25);

  // Build SVG Path strings
  const observedPath = filteredData.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYFlow(d.flow_rate || 0)}`).join(' ');
  const expectedPath = filteredData.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYFlow(d.expected_flow || d.flow_rate || 0)}`).join(' ');

  // 95% Confidence Interval polygon path
  let areaPath = '';
  if (filteredData.length) {
    const topPoints = filteredData.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYFlow(d.expected_upper_95 || d.flow_rate || 0)}`).join(' ');
    const btmPoints = filteredData.slice().reverse().map((d, i) => `L ${getX(filteredData.length - 1 - i)} ${getYFlow(d.expected_lower_95 || d.flow_rate || 0)}`).join(' ');
    areaPath = `${topPoints} ${btmPoints} Z`;
  }

  // Pressure path
  const pressurePath = filteredData.map((d, i) => `${i === 0 ? 'M' : 'L'} ${getX(i)} ${getYPress(d.pressure_mean || 45)}`).join(' ');

  const activePoint = hoverIndex !== null && filteredData[hoverIndex] ? filteredData[hoverIndex] : filteredData[filteredData.length - 1];

  return (
    <div className="glass-panel" style={{ marginBottom: '24px' }}>
      {/* Header & Controls */}
      <div className="flex items-center justify-between flex-wrap gap-4" style={{ marginBottom: '16px' }}>
        <div>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            Hydraulic Flow Dynamics & 95% Bayesian Forecast Interval
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Observed DMA Inflow vs. uncompromised expected baseline. Red markers indicate confirmed leak breaches.
          </p>
        </div>

        {/* Time Window Selectors */}
        <div className="flex items-center gap-2">
          {['24h', '3d', '7d', 'all'].map(r => (
            <button
              key={r}
              onClick={() => setZoomRange(r)}
              className={`tab-btn ${zoomRange === r ? 'active' : ''}`}
              style={{ padding: '6px 12px', fontSize: '0.75rem' }}
            >
              {r.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* Hover Info Ribbon */}
      {activePoint && (
        <div style={{
          background: 'rgba(2, 6, 23, 0.6)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '8px',
          padding: '10px 16px',
          marginBottom: '16px',
          fontSize: '0.8rem',
          display: 'flex',
          flexWrap: 'wrap',
          gap: '20px',
          alignItems: 'center'
        }}>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Time: </span>
            <span style={{ fontWeight: 600, color: '#f8fafc' }}>{activePoint.timestamp}</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Observed: </span>
            <span style={{ fontWeight: 700, color: '#38bdf8' }}>{activePoint.flow_rate?.toFixed(1)} m³/h</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Expected: </span>
            <span style={{ fontWeight: 600, color: '#94a3b8' }}>{activePoint.expected_flow?.toFixed(1) || 'N/A'} m³/h</span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Residual: </span>
            <span style={{ fontWeight: 700, color: (activePoint.flow_residual || 0) > 3.5 ? '#fb7185' : '#34d399' }}>
              {(activePoint.flow_residual || 0) > 0 ? '+' : ''}{activePoint.flow_residual?.toFixed(1) || 0} m³/h
            </span>
          </div>
          <div>
            <span style={{ color: 'var(--text-muted)' }}>Avg Pressure: </span>
            <span style={{ fontWeight: 600, color: '#a78bfa' }}>{activePoint.pressure_mean?.toFixed(1) || 'N/A'} m</span>
          </div>
          {activePoint.leak_alarm_active && (
            <span className="badge badge-critical">LEAK ACTIVE</span>
          )}
          {activePoint.is_mnf_window && (
            <span className="badge badge-medium">MNF (02-04 AM)</span>
          )}
        </div>
      )}

      {/* SVG Time-Series Chart */}
      <div style={{ width: '100%', overflowX: 'auto' }}>
        <svg
          viewBox={`0 0 ${width} ${heightFlow + heightPressure + 60}`}
          style={{ width: '100%', height: 'auto', display: 'block' }}
          onMouseLeave={() => setHoverIndex(null)}
        >
          <defs>
            <linearGradient id="flowBand" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#0284c7" stopOpacity="0.25" />
              <stop offset="100%" stopColor="#0284c7" stopOpacity="0.05" />
            </linearGradient>
          </defs>

          {/* Grid lines (Flow) */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = padTop + pct * heightFlow;
            const val = maxFlow - pct * (maxFlow - minFlow);
            return (
              <g key={`grid-flow-${i}`}>
                <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke="rgba(51, 65, 85, 0.3)" strokeDasharray="3 3" />
                <text x={padLeft - 10} y={y + 4} fill="#64748b" fontSize="11" textAnchor="end" fontFamily="var(--font-mono)">
                  {Math.round(val)}
                </text>
              </g>
            );
          })}

          {/* MNF Background Shading (02:00-04:00 AM) */}
          {filteredData.map((d, i) => {
            if (d.is_mnf_window) {
              const x1 = getX(i);
              const x2 = getX(i + 1);
              return (
                <rect
                  key={`mnf-${i}`}
                  x={x1}
                  y={padTop}
                  width={Math.max(1, x2 - x1)}
                  height={heightFlow}
                  fill="rgba(56, 189, 248, 0.04)"
                />
              );
            }
            return null;
          })}

          {/* 95% Confidence Band */}
          {areaPath && <path d={areaPath} fill="url(#flowBand)" />}

          {/* Expected Baseline (Dashed Cyan) */}
          <path d={expectedPath} fill="none" stroke="#0ea5e9" strokeWidth="2" strokeDasharray="5 4" opacity="0.85" />

          {/* Observed Flow (Solid White/Cyan) */}
          <path d={observedPath} fill="none" stroke="#f8fafc" strokeWidth="2" />

          {/* Leak Anomaly Markers */}
          {filteredData.map((d, i) => {
            if (d.leak_alarm_active) {
              return (
                <circle
                  key={`alarm-${i}`}
                  cx={getX(i)}
                  cy={getYFlow(d.flow_rate || 0)}
                  r="4"
                  fill="#f43f5e"
                  stroke="#881337"
                  strokeWidth="1.5"
                />
              );
            }
            return null;
          })}

          {/* Pressure Divider & Label */}
          <line
            x1={padLeft}
            y1={padTop + heightFlow + 20}
            x2={width - padRight}
            y2={padTop + heightFlow + 20}
            stroke="rgba(51, 65, 85, 0.6)"
          />
          <text
            x={padLeft}
            y={padTop + heightFlow + 38}
            fill="#a78bfa"
            fontSize="11"
            fontWeight="600"
          >
            HYDRAULIC PRESSURE HEAD (m)
          </text>

          {/* Pressure Series */}
          <g transform={`translate(0, ${padTop + heightFlow + 30})`}>
            {[0, 0.5, 1].map((pct, i) => {
              const y = 15 + pct * (heightPressure - 25);
              const val = maxP - pct * (maxP - minP);
              return (
                <g key={`grid-p-${i}`}>
                  <line x1={padLeft} y1={y} x2={width - padRight} y2={y} stroke="rgba(51, 65, 85, 0.2)" strokeDasharray="3 3" />
                  <text x={padLeft - 10} y={y + 4} fill="#64748b" fontSize="10" textAnchor="end" fontFamily="var(--font-mono)">
                    {Math.round(val)}m
                  </text>
                </g>
              );
            })}
            <path d={pressurePath} fill="none" stroke="#a78bfa" strokeWidth="1.8" />
          </g>

          {/* Hover Crosshair */}
          {hoverIndex !== null && (
            <line
              x1={getX(hoverIndex)}
              y1={padTop}
              x2={getX(hoverIndex)}
              y2={padTop + heightFlow + heightPressure + 20}
              stroke="rgba(248, 250, 252, 0.4)"
              strokeWidth="1"
              strokeDasharray="2 2"
            />
          )}

          {/* Transparent Overlay for Mouse Events */}
          {filteredData.map((d, i) => (
            <rect
              key={`hover-col-${i}`}
              x={getX(i) - (chartW / filteredData.length) / 2}
              y={padTop}
              width={chartW / filteredData.length}
              height={heightFlow + heightPressure + 30}
              fill="transparent"
              onMouseEnter={() => setHoverIndex(i)}
              style={{ cursor: 'crosshair' }}
            />
          ))}
        </svg>
      </div>

      {/* Legend Footer */}
      <div className="flex items-center justify-between flex-wrap gap-4" style={{ marginTop: '16px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <span style={{ width: '16px', height: '3px', background: '#f8fafc', display: 'inline-block' }}></span>
            <span>Observed Flow</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ width: '16px', height: '3px', borderTop: '2px dashed #0ea5e9', display: 'inline-block' }}></span>
            <span>95% Expected Median</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ width: '12px', height: '12px', background: 'rgba(2, 132, 199, 0.3)', border: '1px solid #0284c7', display: 'inline-block', borderRadius: '2px' }}></span>
            <span>95% Prediction Band</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ width: '8px', height: '8px', background: '#f43f5e', borderRadius: '50%', display: 'inline-block' }}></span>
            <span>Leak Alarm Breach</span>
          </div>
          <div className="flex items-center gap-2">
            <span style={{ width: '16px', height: '3px', background: '#a78bfa', display: 'inline-block' }}></span>
            <span>Mean Pressure Head</span>
          </div>
        </div>
        <div>
          Showing {filteredData.length} time steps (15-min frequency)
        </div>
      </div>
    </div>
  );
}
