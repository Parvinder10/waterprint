# WATERPRINT: System Limitations & Engineering Constraints

## 1. Physical & Hydraulic Constraints

### 1.1 The Acoustic vs. SCADA Localization Boundary
WATERPRINT operates at the **macro-to-meso distribution network scale** using SCADA boundary flow meters and junction pressure transducers. 
* **Detection Capability:** The platform reliably detects volume discrepancies as small as $1.0\text{ to }2.0\text{ m}^3\text{/h}$ during Minimum Night Flow (MNF) intervals.
* **Localization Boundary:** Hydrodynamic pressure drop signals attenuate rapidly with pipe distance and diameter ($h_f \propto D^{-4.87}$). In large distribution mains ($D \ge 250\text{ mm}$), small pinhole leaks ($< 1.5\text{ m}^3\text{/h}$) generate pressure drops beneath $0.05\text{ m}$ of head—well below the noise floor of standard industrial pressure transducers ($\pm 0.15\text{ m}$).
* **Operational Hand-off:** WATERPRINT narrows the search area from a $50\text{ km}$ network to a $300\text{ m}$ candidate street segment (Top-3 candidate zones). Final pinpointing on the ground must be completed by acoustic listening crews (correlators, ground microphones, or hydrophones).

### 1.2 PRV Non-Linearity and Pressure Decoupling
Pressure Reducing Valves (PRVs) dynamically adjust their internal opening to maintain fixed downstream pressure regardless of upstream demand or pressure fluctuations. 
* If an active PRV sits between a pressure sensor and a leak, the valve will open wider to compensate for the pressure drop, effectively "erasing" the hydraulic pressure signature at downstream sensors.
* Network models must explicitly account for PRV modulation states to prevent localization false leads.

---

## 2. Sensor & Telemetry Limitations

### 2.1 Electromagnetic Bulk Flow Meter Turndown Ratios
Bulk electromagnetic meters maintain high precision ($\pm 1\%$) within nominal velocity ranges ($1.0 - 5.0\text{ m/s}$). However, during Minimum Night Flow (02:00 – 04:00 AM), fluid velocities often drop below $0.15\text{ m/s}$, where meter accuracy degrades to $\pm 3.5\%$. This measurement uncertainty sets a theoretical lower bound on detectable nocturnal leakage.

### 2.2 Telemetry Latency & Asynchronous Clocks
SCADA RTUs in municipal utilities often experience timestamp drift (several minutes per month) and bursty packet reporting. Unaligned timestamps can create artificial instantaneous mass imbalances ($Q_{\text{in}} - Q_{\text{out}} \ne 0$) during rapid diurnal demand transitions (e.g. 06:30 – 07:30 AM).

---

## 3. Data & Consumer Demand Assumptions

### 3.1 Apparent vs. Real Loss Ambiguity
In the absence of 100% AMI coverage with synchronized 15-minute smart meter uploads, customer meter under-registration (mechanical degradation of domestic multi-jet meters at low flows) mathematically aggregates with physical pipe leaks in daily water balance calculations. Only nocturnal MNF decoupling allows separation of physical loss from meter slip.

### 3.2 Unmetered Authorized Public Consumption
Unscheduled municipal operations—such as fire department hydrants, water main scouring/flushing, or street sweeping—inject sharp, high-volume flow surges that perfectly mimic catastrophic pipe bursts. Without an integrated maintenance management system (CMMS) event feed, automated systems will generate unavoidable false alarms during unannounced main flushes.
