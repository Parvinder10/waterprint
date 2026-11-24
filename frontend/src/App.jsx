import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import KpiOverview from './components/KpiOverview';
import FlowPressureChart from './components/FlowPressureChart';
import WaterBalanceView from './components/WaterBalanceView';
import AnomalyInspector from './components/AnomalyInspector';
import TopologyMap from './components/TopologyMap';
import SensorHealth from './components/SensorHealth';
import BenchmarkComparison from './components/BenchmarkComparison';
import ExportReports from './components/ExportReports';

import {
  fetchSummary,
  fetchFlowPressure,
  fetchWaterBalance,
  fetchAnomalies,
  fetchTopology,
  fetchSensors,
  fetchBenchmarks,
  apiConnectionStatus
} from './api';

import {
  Activity,
  BarChart3,
  Scale,
  AlertTriangle,
  Map,
  Cpu,
  Award,
  Download,
  RefreshCw
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('trends');
  const [dma, setDma] = useState('DMA_NORTH');
  const [isLive, setIsLive] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);

  // Data states
  const [summary, setSummary] = useState(null);
  const [timeseries, setTimeseries] = useState(null);
  const [waterBalance, setWaterBalance] = useState(null);
  const [anomalies, setAnomalies] = useState(null);
  const [topology, setTopology] = useState(null);
  const [sensors, setSensors] = useState(null);
  const [benchmarks, setBenchmarks] = useState(null);

  // Selected event for map highlighting
  const [selectedEvent, setSelectedEvent] = useState(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [sumRes, flowRes, wbRes, anomRes, topoRes, sensRes, benchRes] = await Promise.all([
        fetchSummary(),
        fetchFlowPressure(null, null, 2),
        fetchWaterBalance(),
        fetchAnomalies(),
        fetchTopology(),
        fetchSensors(),
        fetchBenchmarks(),
      ]);

      setSummary(sumRes.data);
      setTimeseries(flowRes.data);
      setWaterBalance(wbRes.data);
      setAnomalies(anomRes.data);
      setTopology(topoRes.data);
      setSensors(sensRes.data);
      setBenchmarks(benchRes.data);

      setIsLive(sumRes.isLive);
      setLastUpdated(new Date().toISOString());

      if (anomRes.data?.events?.length > 0) {
        setSelectedEvent(anomRes.data.events[0]);
      }
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [dma]);

  const tabs = [
    { id: 'trends', label: 'Flow & Pressure Trends', icon: Activity },
    { id: 'balance', label: 'IWA Water Balance & MNF', icon: Scale },
    { id: 'anomalies', label: 'Anomaly Timeline & Alerts', icon: AlertTriangle },
    { id: 'topology', label: 'Network Topology & Map', icon: Map },
    { id: 'sensors', label: 'Sensor Health & Diagnostics', icon: Cpu },
    { id: 'benchmarks', label: 'Evaluation & Benchmarks', icon: Award },
    { id: 'reports', label: 'Exportable Reports', icon: Download },
  ];

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Navbar
        isLive={isLive}
        dma={dma}
        setDma={setDma}
        lastUpdated={lastUpdated}
      />

      {/* Main KPI Bar */}
      <KpiOverview summary={summary} />

      {/* Tab Header Navigation */}
      <div className="tabs-header">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-btn ${isActive ? 'active' : ''}`}
            >
              <Icon size={16} />
              <span>{tab.label}</span>
              {tab.id === 'anomalies' && anomalies?.events?.length > 0 && (
                <span
                  style={{
                    background: '#f43f5e',
                    color: '#ffffff',
                    borderRadius: '9999px',
                    padding: '2px 6px',
                    fontSize: '0.65rem',
                    fontWeight: 700
                  }}
                >
                  {anomalies.events.length}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Active Tab View */}
      {loading ? (
        <div className="glass-panel" style={{ padding: '64px', textAlign: 'center' }}>
          <RefreshCw size={32} color="#38bdf8" className="animate-spin" style={{ margin: '0 auto 16px auto' }} />
          <p style={{ color: 'var(--text-muted)' }}>Synchronizing water distribution network telemetry...</p>
        </div>
      ) : (
        <main>
          {activeTab === 'trends' && (
            <FlowPressureChart timeseriesData={timeseries} />
          )}

          {activeTab === 'balance' && (
            <WaterBalanceView balanceData={waterBalance} />
          )}

          {activeTab === 'anomalies' && (
            <div>
              <AnomalyInspector
                eventsData={anomalies}
                onSelectEvent={(evt) => setSelectedEvent(evt)}
                selectedEventId={selectedEvent?.event_id}
              />
              {topology && (
                <TopologyMap
                  topology={topology}
                  candidateNodes={selectedEvent?.candidate_nodes || []}
                />
              )}
            </div>
          )}

          {activeTab === 'topology' && (
            <TopologyMap
              topology={topology}
              candidateNodes={selectedEvent?.candidate_nodes || []}
            />
          )}

          {activeTab === 'sensors' && (
            <SensorHealth sensorData={sensors} />
          )}

          {activeTab === 'benchmarks' && (
            <BenchmarkComparison benchmarksData={benchmarks} />
          )}

          {activeTab === 'reports' && (
            <ExportReports
              summary={summary}
              eventsData={anomalies}
              benchmarksData={benchmarks}
            />
          )}
        </main>
      )}

      {/* Footer */}
      <footer style={{ marginTop: '36px', paddingTop: '20px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
        <div>
          <b>WATERPRINT</b> — Intelligent Water Loss Detection and Network Analytics Platform.
        </div>
        <div className="flex items-center gap-3">
          <span>BattLeDIM / L-Town Benchmark Calibrated</span>
          <span>•</span>
          <span>FastAPI + React Vercel Deployment</span>
        </div>
      </footer>
    </div>
  );
}
