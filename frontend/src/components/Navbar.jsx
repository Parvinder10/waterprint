import React from 'react';
import { Droplets, Activity, Wifi, WifiOff, ShieldCheck, Database } from 'lucide-react';

export default function Navbar({ isLive, dma, setDma, lastUpdated }) {
  return (
    <header className="glass-panel" style={{ marginBottom: '24px', padding: '16px 24px' }}>
      <div className="flex items-center justify-between flex-wrap gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div style={{
            background: 'linear-gradient(135deg, #0284c7, #06b6d4)',
            padding: '10px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(6, 182, 212, 0.4)'
          }}>
            <Droplets size={26} color="#ffffff" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #f8fafc, #38bdf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                WATERPRINT
              </h1>
              <span className="badge badge-medium" style={{ fontSize: '0.65rem' }}>v1.0.0</span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Intelligent Water Loss Detection & Network Analytics
            </p>
          </div>
        </div>

        {/* Center / DMA Selector */}
        <div className="flex items-center gap-3">
          <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
            TARGET NETWORK:
          </label>
          <select 
            value={dma} 
            onChange={(e) => setDma(e.target.value)}
            className="select-control"
          >
            <option value="DMA_NORTH">DMA_NORTH (L-Town Benchmark)</option>
            <option value="DMA_SOUTH" disabled>DMA_SOUTH (Telemetry Planned)</option>
            <option value="DMA_CENTRAL" disabled>DMA_CENTRAL (Telemetry Planned)</option>
          </select>
        </div>

        {/* Right / Status Pill */}
        <div className="flex items-center gap-3">
          <div className={`badge ${isLive ? 'badge-success' : 'badge-medium'}`} style={{ padding: '6px 12px', fontSize: '0.75rem' }}>
            {isLive ? (
              <>
                <Wifi size={14} />
                <span>API CONNECTED (PROD)</span>
              </>
            ) : (
              <>
                <Database size={14} />
                <span>BENCHMARK CACHE (OFFLINE)</span>
              </>
            )}
          </div>
          <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            Updated: {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Ready'}
          </div>
        </div>
      </div>
    </header>
  );
}
