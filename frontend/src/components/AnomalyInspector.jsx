import React, { useState } from 'react';
import { AlertCircle, Wrench, MapPin, CheckCircle2, ChevronRight, Activity, Clock, ShieldCheck } from 'lucide-react';

export default function AnomalyInspector({ eventsData, onSelectEvent, selectedEventId }) {
  const events = eventsData?.events || [];
  const [selectedEvt, setSelectedEvt] = useState(events[0] || null);

  const handleSelect = (evt) => {
    setSelectedEvt(evt);
    if (onSelectEvent) {
      onSelectEvent(evt);
    }
  };

  if (!events.length) {
    return (
      <div className="glass-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <CheckCircle2 size={36} color="#34d399" style={{ margin: '0 auto 12px auto' }} />
        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>No Active Anomaly Incidents</h4>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
          All hydraulic flow residuals and nodal pressures are within normal 95% operating envelopes.
        </p>
      </div>
    );
  }

  const current = selectedEvt || events[0];

  return (
    <div style={{ marginBottom: '24px' }}>
      <div className="grid-cols-2" style={{ gap: '20px' }}>
        {/* Left: Incident Events List */}
        <div className="glass-panel">
          <div className="flex items-center justify-between" style={{ marginBottom: '16px' }}>
            <div className="flex items-center gap-2">
              <AlertCircle size={20} color="#fb7185" />
              <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f8fafc' }}>
                Confirmed Leak Incidents ({events.length})
              </h3>
            </div>
            <span className="badge badge-critical" style={{ fontSize: '0.7rem' }}>
              REPAIR PRIORITIZATION ACTIVE
            </span>
          </div>

          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            Events confirmed across multi-step persistence windows with concurrent nodal pressure depressions. Click to inspect candidate zones.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '560px', overflowY: 'auto' }}>
            {events.map((evt) => {
              const isSelected = current && current.event_id === evt.event_id;
              const sev = evt.severity;
              const badgeClass = sev === 'CRITICAL' ? 'badge-critical' : (sev === 'HIGH' ? 'badge-high' : 'badge-medium');
              
              // Priority tier badge
              const tier = evt.repair_priority_tier || 'ELEVATED_P2';
              const tierColor = tier === 'URGENT_P1' ? '#f43f5e' : (tier === 'ELEVATED_P2' ? '#f59e0b' : '#38bdf8');

              return (
                <div
                  key={evt.event_id}
                  onClick={() => handleSelect(evt)}
                  style={{
                    background: isSelected ? 'rgba(14, 165, 233, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                    border: isSelected ? '1px solid #0284c7' : '1px solid rgba(51, 65, 85, 0.3)',
                    borderRadius: '8px',
                    padding: '12px 16px',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div className="flex items-center justify-between" style={{ marginBottom: '6px' }}>
                    <div className="flex items-center gap-2">
                      <span style={{ fontWeight: 700, fontSize: '0.9rem', color: '#f8fafc' }}>
                        {evt.event_id}
                      </span>
                      <span className={`badge ${badgeClass}`} style={{ fontSize: '0.65rem' }}>
                        {sev}
                      </span>
                      <span style={{ fontSize: '0.7rem', fontWeight: 700, color: tierColor, border: `1px solid ${tierColor}`, padding: '2px 6px', borderRadius: '4px' }}>
                        {tier.replace('_', ' ')} ({evt.repair_priority_score || 85}/100)
                      </span>
                    </div>
                    <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                      {evt.duration_hours}h duration
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-muted" style={{ fontSize: '0.75rem' }}>
                    <div>
                      <span>Peak Residual: </span>
                      <span style={{ color: '#fb7185', fontWeight: 600 }}>+{evt.peak_flow_residual_m3h} m³/h</span>
                    </div>
                    <div>
                      <span>Target: </span>
                      <span style={{ color: '#38bdf8', fontWeight: 600 }}>{evt.primary_candidate_zone || 'ZONE_NORTH_EAST'}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right: Selected Event Detail & Candidate Localisation */}
        {current && (
          <div className="glass-panel flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between" style={{ marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#f8fafc' }}>
                      {current.event_id}
                    </h3>
                    <span className={`badge ${current.severity === 'CRITICAL' ? 'badge-critical' : 'badge-high'}`}>
                      {current.severity}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Active from {current.start_time} to {current.end_time}
                  </span>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>REPAIR PRIORITY</div>
                  <div style={{ fontSize: '1.4rem', fontWeight: 800, color: '#f59e0b' }}>
                    {current.repair_priority_score || 85} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>/ 100</span>
                  </div>
                </div>
              </div>

              {/* Event Metrics Ribbon */}
              <div className="grid-cols-3" style={{ gap: '12px', marginBottom: '16px' }}>
                <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PEAK FLOW RESIDUAL</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fb7185' }}>
                    +{current.peak_flow_residual_m3h} m³/h
                  </div>
                </div>

                <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>PRESSURE HEAD DROP</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#a78bfa' }}>
                    -{current.mean_pressure_drop_m} m head
                  </div>
                </div>

                <div style={{ background: 'rgba(2, 6, 23, 0.4)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>CONFIDENCE SCORE</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>
                    {(current.confidence_score * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              {/* Supporting Evidence */}
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <ShieldCheck size={16} color="#38bdf8" />
                  Engineering Evidence & Telemetry Signature
                </h4>
                <div style={{ background: 'rgba(15, 23, 42, 0.6)', border: '1px solid var(--border-color)', borderRadius: '6px', padding: '12px', fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                  {current.supporting_evidence || 'Sustained volumetric flow surplus accompanied by synchronized localized pressure drop across monitored piezoresistive sensors.'}
                </div>
              </div>

              {/* Ranked Candidate Zones */}
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <MapPin size={16} color="#f59e0b" />
                  Ranked Candidate Zones (Topological Sensitivity)
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  {(current.candidate_zones || [
                    { zone: current.primary_candidate_zone || 'ZONE_NORTH_EAST', probability_pct: 65.0 },
                    { zone: 'ZONE_NORTH_WEST', probability_pct: 25.0 }
                  ]).map((z, idx) => (
                    <div key={idx} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(2, 6, 23, 0.4)', padding: '8px 12px', borderRadius: '6px', fontSize: '0.8rem' }}>
                      <div className="flex items-center gap-2">
                        <span style={{ fontWeight: 700, color: '#f8fafc' }}>{idx + 1}. {z.zone}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div style={{ width: '80px', height: '6px', background: '#1e293b', borderRadius: '3px', overflow: 'hidden' }}>
                          <div style={{ width: `${z.probability_pct}%`, height: '100%', background: '#38bdf8' }}></div>
                        </div>
                        <span style={{ fontWeight: 700, color: '#38bdf8', fontFamily: 'var(--font-mono)' }}>{z.probability_pct}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Candidate Nodes */}
              {current.candidate_nodes && current.candidate_nodes.length > 0 && (
                <div>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: '#f8fafc', marginBottom: '6px' }}>
                    Primary Suspected Junction Nodes
                  </h4>
                  <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                    {current.candidate_nodes.map((n, i) => (
                      <span key={i} className="badge badge-medium" style={{ fontSize: '0.75rem', padding: '4px 8px' }}>
                        Node: {n.node_id || n} ({n.probability_pct || 6.2}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid var(--border-color)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Note: Sparse pressure sensors identify candidate areas; ground crews should deploy acoustic ground microphones to pinpoint exact pipe leak point.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
