/**
 * API client module for WATERPRINT frontend.
 * Reads VITE_API_BASE_URL from environment.
 * If backend is not reached, transparently falls back to calibrated benchmark dataset.
 */

import {
  FALLBACK_SUMMARY,
  FALLBACK_TOPOLOGY,
  FALLBACK_EVENTS,
  FALLBACK_BENCHMARKS,
  FALLBACK_SENSORS,
  FALLBACK_WATER_BALANCE,
  FALLBACK_TIMESERIES,
} from './data/fallbackData';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export let apiConnectionStatus = {
  isLive: false,
  endpoint: API_BASE || 'Relative / Same Origin',
  lastChecked: null,
};

async function safeFetch(path, fallbackData) {
  const url = `${API_BASE}${path}`;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 4000); // 4-second timeout
    
    const response = await fetch(url, {
      signal: controller.signal,
      headers: {
        'Accept': 'application/json',
      },
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      apiConnectionStatus.isLive = true;
      apiConnectionStatus.lastChecked = new Date().toISOString();
      return { data, isLive: true };
    }
  } catch (err) {
    // Backend offline or unreachable
  }
  
  apiConnectionStatus.isLive = false;
  apiConnectionStatus.lastChecked = new Date().toISOString();
  return { data: fallbackData, isLive: false };
}

export async function fetchSummary() {
  return safeFetch('/api/summary', FALLBACK_SUMMARY);
}

export async function fetchFlowPressure(startDate = null, endDate = null, downsampleStep = 2) {
  let query = `?downsample_step=${downsampleStep}`;
  if (startDate) query += `&start_date=${startDate}`;
  if (endDate) query += `&end_date=${endDate}`;
  return safeFetch(`/api/flow-pressure${query}`, FALLBACK_TIMESERIES);
}

export async function fetchWaterBalance() {
  return safeFetch('/api/water-balance', FALLBACK_WATER_BALANCE);
}

export async function fetchAnomalies() {
  return safeFetch('/api/anomalies', { events: FALLBACK_EVENTS });
}

export async function fetchTopology() {
  return safeFetch('/api/topology', FALLBACK_TOPOLOGY);
}

export async function fetchSensors() {
  return safeFetch('/api/sensors', FALLBACK_SENSORS);
}

export async function fetchBenchmarks() {
  return safeFetch('/api/benchmarks', { benchmarks: FALLBACK_BENCHMARKS });
}
