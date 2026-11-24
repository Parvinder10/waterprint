import React from 'react';
import { Scale, Moon, ShieldAlert, CheckCircle, TrendingUp, Info } from 'lucide-react';

export default function WaterBalanceView({ balanceData }) {
  if (!balanceData) return null;

  const wb = balanceData.water_balance || {};
  const dailyMnf = balanceData.daily_minimum_night_flow || [];

  const siv = wb.system_input_volume_m3 || 0;
  const billed = wb.billed_authorized_consumption_m3 || 0;
  const unbilled = wb.unbilled_authorized_consumption_m3 || 0;
  const apparent = wb.apparent_losses_m3 || 0;
  const real = wb.real_physical_losses_m3 || 0;
  const nrw = wb.non_revenue_water_m3 || 0;
  const nrwPct = wb.non_revenue_water_pct || 0;
  const ili = wb.infrastructure_leakage_index_ili || 0;
  const rating = wb.ili_rating || 'Category A';

  const rows = [
    { label: 'System Input Volume (SIV)', vol: siv, pct: 100.0, color: '#f8fafc', note: 'Bulk supply at district meter' },
    { label: 'Billed Authorized Consumption', vol: billed, pct: (billed / Math.max(1, siv)) * 100, color: '#38bdf8', note: 'Customer metered residential & commercial' },
    { label: 'Unbilled Authorized Consumption', vol: unbilled, pct: (unbilled / Math.max(1, siv)) * 100, color: '#94a3b8', note: 'Firefighting, main flushing, public fountains' },
    { label: 'Apparent Losses (Commercial)', vol: apparent, pct: (apparent / Math.max(1, siv)) * 100, color: '#f59e0b', note: 'Customer meter under-registration & unauthorized use' },
    { label: 'Real Losses (Physical)', vol: real, pct: (real / Math.max(1, siv)) * 100, color: '#fb7185', note: 'Mains bursts, joint weeping & service pipe leaks' },
    { label: 'Total Non-Revenue Water (NRW)', vol: nrw, pct: nrwPct, color: '#f43f5e', note: 'SIV minus Billed Authorized Volume' },
  ];

  return (
    <div style={{ marginBottom: '24px' }}>
      <div className="grid-cols-2" style={{ marginBottom: '20px' }}>
        {/* Left: IWA Water Balance Audit Table */}
        <div className="glass-panel">
          <div className="flex items-center gap-2" style={{ marginBottom: '16px' }}>
            <Scale size={20} color="#38bdf8" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              IWA Standard Water Balance Reconciliation
            </h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Standardized water audit accounting according to International Water Association (IWA) / AWWA methodology.
          </p>

          <div className="data-table-container">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Audit Component</th>
                  <th style={{ textAlign: 'right' }}>Volume (m³)</th>
                  <th style={{ textAlign: 'right' }}>% of SIV</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i}>
                    <td>
                      <div style={{ fontWeight: 600, color: r.color }}>{r.label}</div>
                      <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{r.note}</div>
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {r.vol.toLocaleString(undefined, { maximumFractionDigits: 1 })}
                    </td>
                    <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: r.color, fontWeight: 700 }}>
                      {r.pct.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right: ILI Performance Card */}
        <div className="glass-panel flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2" style={{ marginBottom: '16px' }}>
              <ShieldAlert size={20} color="#10b981" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                Infrastructure Leakage Index (ILI) Analysis
              </h3>
            </div>

            <div style={{
              background: 'rgba(2, 6, 23, 0.5)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              borderRadius: '12px',
              padding: '20px',
              textAlign: 'center',
              marginBottom: '16px'
            }}>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                CURRENT ILI RATING
              </div>
              <div style={{ fontSize: '3rem', fontWeight: 800, color: '#34d399', letterSpacing: '-0.02em', margin: '4px 0' }}>
                {ili.toFixed(2)}
              </div>
              <span className="badge badge-success" style={{ fontSize: '0.8rem', padding: '6px 14px' }}>
                {rating}
              </span>
            </div>

            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.6' }}>
              <p style={{ marginBottom: '8px' }}>
                <b>ILI Definition:</b> Ratio of Current Annual Real Losses (CARL) to Unavoidable Annual Real Losses (UARL):
              </p>
              <div style={{ fontFamily: 'var(--font-mono)', background: 'rgba(15, 23, 42, 0.6)', padding: '8px 12px', borderRadius: '6px', fontSize: '0.75rem', marginBottom: '12px' }}>
                ILI = CARL / UARL = {real.toFixed(1)} m³ / {wb.uarl_period_m3?.toFixed(1) || 'N/A'} m³
              </div>
              <p>
                <b>Operational Benchmark:</b> ILI &lt; 1.5 indicates world-class physical loss control. Ratios above 4.0 warrant targeted acoustic active leakage inspection.
              </p>
            </div>
          </div>

          <div style={{ fontSize: '0.75rem', color: '#38bdf8', marginTop: '16px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Info size={14} />
            <span>Calibrated against L-Town DMA_NORTH network characteristics.</span>
          </div>
        </div>
      </div>

      {/* Bottom: Daily Minimum Night Flow (MNF) Progression */}
      {dailyMnf.length > 0 && (
        <div className="glass-panel">
          <div className="flex items-center gap-2" style={{ marginBottom: '12px' }}>
            <Moon size={20} color="#a78bfa" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
              Diurnal Minimum Night Flow (MNF) & Net Night Flow (NNF) Tracking
            </h3>
          </div>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Measured between 02:00 and 04:00 AM. Legitimate customer night demand is subtracted to compute Net Night Flow. Sustained rises indicate active subterranean leaks.
          </p>

          <div className="data-table-container" style={{ maxHeight: '280px', overflowY: 'auto' }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th style={{ textAlign: 'right' }}>MNF Inflow (m³/h)</th>
                  <th style={{ textAlign: 'right' }}>Legitimate Demand (m³/h)</th>
                  <th style={{ textAlign: 'right' }}>Net Night Flow (m³/h)</th>
                  <th style={{ textAlign: 'right' }}>Unexplained Night Loss (m³/h)</th>
                  <th style={{ textAlign: 'center' }}>Anomaly Status</th>
                </tr>
              </thead>
              <tbody>
                {dailyMnf.slice(-20).map((d, i) => {
                  const loss = d.unexplained_night_loss || 0;
                  const isElevated = loss > 1.5;
                  return (
                    <tr key={i}>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>{d.date}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)' }}>{d.mnf_flow_mean?.toFixed(2)}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>{d.legitimate_night_demand?.toFixed(2)}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: 600 }}>{d.net_night_flow_nnf?.toFixed(2)}</td>
                      <td style={{ textAlign: 'right', fontFamily: 'var(--font-mono)', color: isElevated ? '#fb7185' : '#34d399', fontWeight: 700 }}>
                        {loss.toFixed(2)}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {isElevated ? (
                          <span className="badge badge-critical" style={{ fontSize: '0.65rem' }}>ELEVATED NIGHT LOSS</span>
                        ) : (
                          <span className="badge badge-success" style={{ fontSize: '0.65rem' }}>NOMINAL</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
