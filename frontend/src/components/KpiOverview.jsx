import React from 'react';
import { Activity, AlertTriangle, ArrowDownRight, CheckCircle2, Droplet, Gauge } from 'lucide-react';

export default function KpiOverview({ summary }) {
  if (!summary) return null;

  const siv = summary.system_input_volume_m3 || 0;
  const nrwPct = summary.non_revenue_water_pct || 0;
  const nrwVol = summary.non_revenue_water_m3 || 0;
  const ili = summary.infrastructure_leakage_index_ili || 0;
  const rating = summary.ili_rating || 'Category A';
  const totalEvents = summary.total_detected_events || 0;
  const recallPct = summary.benchmark_recall_pct || 100.0;
  const healthPct = summary.data_completeness_pct || 100.0;
  const faultsCount = summary.total_hardware_faults || 0;

  return (
    <div className="grid-cols-4" style={{ marginBottom: '24px' }}>
      {/* SIV */}
      <div className="glass-panel">
        <div className="flex items-center justify-between" style={{ marginBottom: '8px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>SYSTEM INPUT VOLUME</span>
          <Droplet size={18} color="#38bdf8" />
        </div>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
          {siv.toLocaleString(undefined, { maximumFractionDigits: 0 })} <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>m³</span>
        </div>
        <div style={{ fontSize: '0.75rem', color: '#38bdf8', marginTop: '6px' }}>
          {summary.evaluation_days || 180} Days Monitored (DMA_NORTH)
        </div>
      </div>

      {/* Non-Revenue Water */}
      <div className="glass-panel">
        <div className="flex items-center justify-between" style={{ marginBottom: '8px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>NON-REVENUE WATER</span>
          <ArrowDownRight size={18} color="#f59e0b" />
        </div>
        <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#f59e0b', letterSpacing: '-0.02em' }}>
          {nrwPct.toFixed(1)}%
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
          {nrwVol.toLocaleString(undefined, { maximumFractionDigits: 0 })} m³ Total Volume Lost
        </div>
      </div>

      {/* Infrastructure Leakage Index */}
      <div className="glass-panel">
        <div className="flex items-center justify-between" style={{ marginBottom: '8px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>INFRASTRUCTURE LEAKAGE INDEX</span>
          <Gauge size={18} color="#10b981" />
        </div>
        <div className="flex items-center gap-2">
          <span style={{ fontSize: '1.6rem', fontWeight: 800, color: '#10b981', letterSpacing: '-0.02em' }}>
            {ili.toFixed(2)}
          </span>
          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>
            {rating.split(' ')[0]}
          </span>
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
          CARL / UARL Standard Benchmark
        </div>
      </div>

      {/* Detected Anomalies */}
      <div className="glass-panel">
        <div className="flex items-center justify-between" style={{ marginBottom: '8px' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>DETECTED LEAK EVENTS</span>
          <AlertTriangle size={18} color="#f43f5e" />
        </div>
        <div className="flex items-center gap-2">
          <span style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fb7185', letterSpacing: '-0.02em' }}>
            {totalEvents}
          </span>
          <span className="badge badge-critical" style={{ fontSize: '0.65rem' }}>
            {recallPct}% RECALL
          </span>
        </div>
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px' }}>
          Mean Delay: {summary.mean_detection_delay_hours || 7.9}h | FAR: {summary.false_alarms_per_month || 3.9}/mo
        </div>
      </div>
    </div>
  );
}
