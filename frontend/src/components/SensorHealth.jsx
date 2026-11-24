import React from 'react';
import { Activity, ShieldCheck, AlertOctagon, Cpu, CheckCircle2, AlertTriangle } from 'lucide-react';

export default function SensorHealth({ sensorData }) {
  if (!sensorData) return null;

  const qc = sensorData.quality_summary || {};
  const faults = sensorData.fault_records || [];

  return (
    <div style={{ marginBottom: '24px' }}>
      {/* Top Banner: Sensor Anomaly Isolation Principle */}
      <div className="glass-panel" style={{ borderLeft: '4px solid #38bdf8', marginBottom: '20px' }}>
        <div className="flex items-center gap-2" style={{ marginBottom: '8px' }}>
          <ShieldCheck size={20} color="#38bdf8" />
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#f8fafc' }}>
            Sensor Fault Segregation Principle
          </h3>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
          A cornerstone of WATERPRINT is the strict mathematical and operational separation of <b>hardware/telemetry glitches</b> from <b>physical hydraulic leakage evidence</b>. 
          Stuck ADC converters (flatlines), dropped telemetry packets, and electrical rate-of-change spikes are caught here and strictly prevented from triggering false positive leak alarms.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="grid-cols-4" style={{ marginBottom: '20px' }}>
        <div className="glass-panel">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>FLOW CHANNELS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#38bdf8' }}>
            {qc.flow_sensors_monitored || 1} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Station</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Electromagnetic Bulk Meter</div>
        </div>

        <div className="glass-panel">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>PRESSURE TRANSDUCERS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#a78bfa' }}>
            {qc.pressure_sensors_monitored || 8} <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Sensors</span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>Piezoresistive Transducers</div>
        </div>

        <div className="glass-panel">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>DATA COMPLETENESS</div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399' }}>
            {qc.data_completeness_pct?.toFixed(2) || '100.00'}%
          </div>
          <div style={{ fontSize: '0.75rem', color: '#34d399', marginTop: '4px' }}>High Telemetry Fidelity</div>
        </div>

        <div className="glass-panel">
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600 }}>HARDWARE HEALTH</div>
          <div className="flex items-center gap-2" style={{ marginTop: '4px' }}>
            <span style={{ fontSize: '1.6rem', fontWeight: 800, color: '#34d399' }}>
              {qc.hardware_health_status || 'EXCELLENT'}
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            {faults.length} Isolated Hardware Events
          </div>
        </div>
      </div>

      {/* Fault Registry Table */}
      <div className="glass-panel">
        <div className="flex items-center justify-between" style={{ marginBottom: '16px' }}>
          <div className="flex items-center gap-2">
            <AlertOctagon size={20} color="#f59e0b" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              Hardware & Telemetry Diagnostic Registry
            </h3>
          </div>
          <span className="badge badge-medium" style={{ fontSize: '0.7rem' }}>
            ISOLATED FROM LEAK MODELS
          </span>
        </div>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>Sensor ID</th>
                <th>Type</th>
                <th>Fault Classification</th>
                <th>Severity</th>
                <th>Diagnostic Description</th>
              </tr>
            </thead>
            <tbody>
              {faults.length > 0 ? (
                faults.map((f, i) => {
                  const isCritical = f.severity === 'CRITICAL';
                  return (
                    <tr key={i}>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{f.timestamp}</td>
                      <td style={{ fontWeight: 600, color: '#38bdf8' }}>{f.sensor_id}</td>
                      <td>{f.sensor_type}</td>
                      <td>
                        <span className={`badge ${f.fault_type === 'FLATLINE' ? 'badge-medium' : 'badge-high'}`} style={{ fontSize: '0.65rem' }}>
                          {f.fault_type}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${isCritical ? 'badge-critical' : 'badge-medium'}`} style={{ fontSize: '0.65rem' }}>
                          {f.severity}
                        </span>
                      </td>
                      <td style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{f.description}</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '24px' }}>
                    Zero hardware or telemetry faults detected. All channels operational.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
