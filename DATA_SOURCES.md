# WATERPRINT: Data Sources and Network Specifications

This document catalogs genuine, publicly accessible water distribution network benchmarks, sensor telemetry datasets, network topologies, and smart meter consumption archives utilized within the **WATERPRINT** analytics platform.

---

## 1. Primary Benchmark: BattLeDIM 2020 (L-Town Water Distribution Network)

### Overview & Provenance
* **Title:** Battle of the Leakage Detection and Isolation Methods (BattLeDIM 2020) Dataset
* **Organizers & Authors:** KIOS Research and Innovation Center of Excellence (University of Cyprus), TU Delft, University of Sheffield, University of Adelaide, University of Exeter, and Politecnico di Torino.
* **Hosting Platform:** Zenodo
* **DOI / Permanent Link:** [10.5281/zenodo.4017659](https://doi.org/10.5281/zenodo.4017659)
* **Official Code & Evaluation Repository:** [https://github.com/BattLeDIM/BattLeDIM2020](https://github.com/BattLeDIM/BattLeDIM2020)
* **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0)

### Nature of Data & Clear Disclosure
> [!IMPORTANT]
> **Benchmark Simulation Disclosure:** The L-Town network dataset is a benchmark simulation generated using EPANET 2.2 and hydraulic pressure-dependent leak physics ($q_{\text{leak}} = C \cdot p^\alpha$). The network topology, pipe roughness, node elevations, and baseline demand patterns are derived directly from a real operating municipal drinking water system in Cyprus. Sensor noise, diurnal residential variations, commercial consumption fluctuations, and pipe burst/leak scenarios were systematically introduced to serve as a rigorous blind benchmark for leakage detection and isolation.

### Network Topology & Asset Inventory
* **Network Name:** L-Town (divided into 3 District Metered Areas: DMA 1, DMA 2, DMA 3)
* **Nodes:** 782 junction nodes, 1 central reservoir (R-1), 2 elevated balancing tanks (T-1, T-2)
* **Links:** 905 pipes (ductile iron, PVC, HDPE), 2 Pressure Reducing Valves (PRVs), 3 variable/fixed-speed booster pump stations
* **EPANET Model File:** `data/raw/network_topology.json` (derived from `L-TOWN.inp`)

### Sensor Telemetry & Field Schema
The benchmark provides multi-year SCADA telemetry sampled at 15-minute and 5-minute intervals:

| Field Name | Physical Entity | Units | Sensor Type | Description / Location |
| :--- | :--- | :--- | :--- | :--- |
| `timestamp` | Datetime (ISO 8601) | `YYYY-MM-DD HH:MM:SS` | System Clock | Synchronized 15-minute telemetry intervals |
| `flow_inflow_dma1` | Flow Rate | $m^3/h$ | Electromagnetic Flow Meter | Inflow meter at District Inlet Station 1 (DMA-1) |
| `flow_inflow_dma2` | Flow Rate | $m^3/h$ | Electromagnetic Flow Meter | Inflow meter at District Inlet Station 2 (DMA-2) |
| `flow_inflow_dma3` | Flow Rate | $m^3/h$ | Electromagnetic Flow Meter | Inflow meter at District Inlet Station 3 (DMA-3) |
| `pressure_n1` – `pressure_n33` | Hydraulic Pressure Head | $m$ (meters of $H_2O$) | Piezoresistive Pressure Transducer | Pressure monitoring at 33 strategic distribution junctions |
| `consumption_residential` | Authorized Consumption | $m^3/h$ | Smart Water Meters (AMR/AMI) | Aggregated metered customer consumption across DMA zones |
| `tank_level_t1`, `t2` | Water Storage Head | $m$ | Ultrasonic Level Sensor | Storage level at balancing reservoirs T-1 and T-2 |
| `pump_status_p1` – `p3` | Operational State | Discrete $\{0, 1\}$ | SCADA Relay Feedback | Operating status of distribution pumps |

### Known Ground Truth Leak Events
The benchmark includes realistic incipient leaks (slowly growing pinhole leaks and joint degradation) as well as abrupt pipe bursts:
* **Parameters Recorded:** Event ID, Target Node / Pipe ID, DMA Zone, Exact Start Timestamp, Exact End Timestamp, Peak Leak Flow Rate ($m^3/h$), Leak Diameter ($mm$), and Leak Growth Rate.

---

## 2. Smart Water Meter Consumption Dataset: Diehl Hydrus Pilot

### Overview & Provenance
* **Title:** Smart Meter Water Consumption Measurements with Activity Classification
* **Hosting Platform:** Zenodo
* **DOI / Permanent Link:** [10.5281/zenodo.7506076](https://doi.org/10.5281/zenodo.7506076)
* **Author / Institution:** Chair of Water Supply and Wastewater Technology, Technical University of Berlin
* **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0)

### Nature of Data & Description
* Real-world smart water meter telemetry collected from ultrasonic commercial smart meters (Hydrus 1.3, DN 20, Diehl Metering).
* Captures high-frequency consumption pulses, diurnal residential cycles (morning peak, evening peak), and near-zero nocturnal flow during Minimum Night Flow (MNF) intervals (02:00 – 04:00 AM).
* Used within WATERPRINT to parameterize authorized residential night consumption baselines and smart-meter customer aggregation uncertainty.

---

## 3. ASCE Task Committee Benchmark Networks (Modena, Net3, C-Town)

### Overview & Provenance
* **Repository:** University of Kentucky Water Distribution Systems Research Database
* **Permanent URL:** [https://uknowledge.uky.edu/ce_data/](https://uknowledge.uky.edu/ce_data/)
* **License:** Public Domain / Open Academic Access
* **Role in WATERPRINT:** Used for cross-network topology graph validation and synthetic stress-testing of pressure sensitivity matrices ($S = \partial P / \partial Q$).

---

## 4. Summary of Data Limitations & Measurement Uncertainties

1. **Sensor Measurement Noise:** Real electromagnetic flow meters typically exhibit $\pm 1.5\%$ to $\pm 2.5\%$ relative uncertainty at nominal velocities, degrading significantly below $0.1\text{ m/s}$. Pressure transducers typically exhibit $\pm 0.10\text{ m}$ to $\pm 0.25\text{ m}$ head measurement error.
2. **Telemetry Gaps & Packet Drops:** SCADA communication links intermittently suffer transmission lag, zero-drops, and stuck values (flatlines).
3. **Meter Reading Latency:** Residential Automated Meter Reading (AMR/AMI) systems often upload cumulative index counts at 1-hour or 24-hour intervals rather than synchronized 15-minute intervals, requiring water-balance disaggregation.
4. **Apparent Losses vs. Real Losses:** Customer meter under-registration (meter drift due to mechanical wear) can mimic real physical pipe leakage in macroscopic water balances unless nocturnal minimum night flow analysis is integrated.
