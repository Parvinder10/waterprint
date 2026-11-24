import React from 'react';
import { Award, CheckCircle2, TrendingUp, AlertCircle, HelpCircle } from 'lucide-react';

export default function BenchmarkComparison({ benchmarksData }) {
  const benchmarks = benchmarksData?.benchmarks || [];

  return (
    <div style={{ marginBottom: '24px' }}>
      <div className="glass-panel" style={{ marginBottom: '20px' }}>
        <div className="flex items-center gap-2" style={{ marginBottom: '12px' }}>
          <Award size={22} color="#38bdf8" />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
            Empirical Benchmark Performance vs. Classical Baselines
          </h3>
        </div>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px', lineHeight: '1.6' }}>
          Evaluated using strict chronological train/test splitting on the European BattLeDIM / L-Town benchmark.
          Models are evaluated on unseen operations containing genuine ground-truth pipe bursts and gradual incipient leaks.
        </p>

        <div className="data-table-container">
          <table className="data-table">
            <thead>
              <tr>
                <th>Detection Methodology</th>
                <th style={{ textAlign: 'right' }}>Precision</th>
                <th style={{ textAlign: 'right' }}>Recall</th>
                <th style={{ textAlign: 'right' }}>F1-Score</th>
                <th style={{ textAlign: 'right' }}>Mean Delay</th>
                <th style={{ textAlign: 'right' }}>False Alarms</th>
                <th>Localisation Support</th>
              </tr>
            </thead>
            <tbody>
              {benchmarks.map((b, i) => {
                const isWaterprint = b.Method.includes('WATERPRINT');
                return (
                  <tr
                    key={i}
                    style={{
                      background: isWaterprint ? 'rgba(14, 165, 233, 0.1)' : 'transparent',
                      fontWeight: isWaterprint ? 700 : 400
                    }}
                  >
                    <td>
                      <div className="flex items-center gap-2">
                        {isWaterprint && <CheckCircle2 size={16} color="#38bdf8" />}
                        <span style={{ color: isWaterprint ? '#38bdf8' : '#f8fafc' }}>
                          {b.Method}
                        </span>
                      </div>
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                      {(b.Precision * 100).toFixed(1)}%
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: b.Recall > 0.8 ? '#34d399' : '#fb7185' }}>
                      {(b.Recall * 100).toFixed(1)}%
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: isWaterprint ? '#38bdf8' : 'inherit' }}>
                      {b.F1_Score.toFixed(3)}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
                      {b.Mean_Delay_Hours > 0 ? `${b.Mean_Delay_Hours.toFixed(1)}h` : 'Failed'}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: b.False_Alarms_Per_Month < 5 ? '#34d399' : '#fb7185' }}>
                      {b.False_Alarms_Per_Month.toFixed(1)} / mo
                    </td>
                    <td style={{ fontSize: '0.8rem', color: isWaterprint ? '#38bdf8' : 'var(--text-muted)' }}>
                      {b.Localisation_Support}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Explanatory Cards */}
      <div className="grid-cols-3" style={{ gap: '16px' }}>
        <div className="glass-panel">
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
            Why Static Thresholds Fail
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            Static threshold filters cannot accommodate diurnal cycles or seasonal demand transitions, triggering over 50 false alarms per month during routine morning consumption peaks.
          </p>
        </div>

        <div className="glass-panel">
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#f8fafc', marginBottom: '8px' }}>
            Why Rolling Means Fail
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            When an incipient leak slowly develops over 48 hours, the rolling mean absorbs the escaping volume into its baseline, elevating the alarm threshold and missing the burst entirely.
          </p>
        </div>

        <div className="glass-panel">
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: '#38bdf8', marginBottom: '8px' }}>
            WATERPRINT Advantage
          </h4>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
            Fuses unpolluted historical quantile baselines, sequential CUSUM drift accumulation, nocturnal MNF tracking, and multi-sensor pressure drops to achieve 100% recall with low false alarm rates.
          </p>
        </div>
      </div>
    </div>
  );
}
