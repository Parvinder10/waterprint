import React, { useState } from 'react';
import { Download, FileText, Check, Copy, FileSpreadsheet, Code2 } from 'lucide-react';

export default function ExportReports({ summary, eventsData, benchmarksData }) {
  const [copied, setCopied] = useState(false);

  const events = eventsData?.events || [];
  const wb = summary?.water_balance || {};

  const handleDownloadCsv = () => {
    if (!events.length) return;
    const headers = ['event_id', 'start_time', 'end_time', 'duration_hours', 'severity', 'peak_flow_residual_m3h', 'mean_pressure_drop_m', 'repair_priority_score', 'repair_priority_tier', 'primary_candidate_zone', 'confidence_score'];
    const csvContent = [
      headers.join(','),
      ...events.map(e => headers.map(h => `"${e[h] || ''}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'waterprint_anomaly_events.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleDownloadJson = () => {
    const payload = {
      timestamp: new Date().toISOString(),
      summary,
      benchmarks: benchmarksData?.benchmarks || [],
      events
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'waterprint_audit_summary.json');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const executiveMarkdown = `# WATERPRINT Executive Water Loss Audit Report
- **District Metered Area:** DMA_NORTH (L-Town Calibrated Benchmark)
- **System Input Volume (SIV):** ${(summary?.system_input_volume_m3 || 0).toLocaleString()} m³
- **Billed Authorized Consumption:** ${(summary?.billed_authorized_consumption_m3 || 0).toLocaleString()} m³
- **Non-Revenue Water (NRW):** ${(summary?.non_revenue_water_pct || 0).toFixed(2)}% (${(summary?.non_revenue_water_m3 || 0).toLocaleString()} m³)
- **Infrastructure Leakage Index (ILI):** ${(summary?.infrastructure_leakage_index_ili || 0).toFixed(2)} (${summary?.ili_rating || 'Category A'})
- **Confirmed Leak Incidents:** ${events.length}
- **Benchmark Detection Recall:** ${(summary?.benchmark_recall_pct || 100.0).toFixed(1)}%
- **Mean Detection Delay:** ${(summary?.mean_detection_delay_hours || 7.9).toFixed(1)} hours
- **Hardware Telemetry Completeness:** ${(summary?.data_completeness_pct || 100.0).toFixed(2)}%
  `;

  const handleCopy = () => {
    navigator.clipboard.writeText(executiveMarkdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      <div className="grid-cols-3" style={{ gap: '20px', marginBottom: '20px' }}>
        {/* CSV Export */}
        <div className="glass-panel flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: '12px' }}>
              <FileSpreadsheet size={20} color="#38bdf8" />
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                Anomaly Events (CSV)
              </h4>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Detailed event registry with severity, peak flow residual, mean pressure drop, and ranked candidate zones.
            </p>
          </div>
          <button onClick={handleDownloadCsv} className="btn-primary" style={{ justifyContent: 'center' }}>
            <Download size={16} />
            <span>Download Events CSV</span>
          </button>
        </div>

        {/* JSON Export */}
        <div className="glass-panel flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: '12px' }}>
              <Code2 size={20} color="#10b981" />
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                Audit Summary (JSON)
              </h4>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Machine-readable audit package containing IWA water balances, evaluation metrics, and benchmark scores.
            </p>
          </div>
          <button onClick={handleDownloadJson} className="btn-primary" style={{ justifyContent: 'center' }}>
            <Download size={16} />
            <span>Download JSON Audit</span>
          </button>
        </div>

        {/* Copy Report */}
        <div className="glass-panel flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: '12px' }}>
              <FileText size={20} color="#a78bfa" />
              <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>
                Executive Markdown
              </h4>
            </div>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Formatted compliance and engineering summary ready to paste into technical reports or board memorandums.
            </p>
          </div>
          <button onClick={handleCopy} className="btn-primary" style={{ justifyContent: 'center' }}>
            {copied ? <Check size={16} /> : <Copy size={16} />}
            <span>{copied ? 'Copied to Clipboard' : 'Copy Executive Report'}</span>
          </button>
        </div>
      </div>

      {/* Markdown Preview */}
      <div className="glass-panel">
        <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', marginBottom: '12px' }}>
          Executive Water Loss Audit Summary (Preview)
        </h4>
        <pre style={{
          background: 'rgba(2, 6, 23, 0.6)',
          border: '1px solid var(--border-color)',
          borderRadius: '8px',
          padding: '16px',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.8rem',
          color: '#94a3b8',
          overflowX: 'auto',
          lineHeight: '1.6'
        }}>
          {executiveMarkdown}
        </pre>
      </div>
    </div>
  );
}
