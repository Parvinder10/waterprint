# WATERPRINT: Problem Statement & Engineering Context

## 1. Executive Summary

Municipal water distribution networks (WDNs) are complex, subterranean, highly pressurized cyber-physical systems that deliver potable water across urban landscapes. A chronic and pressing challenge confronting water utilities globally is **Non-Revenue Water (NRW)**—water that has been treated, pumped into the network, but lost before reaching paying customers or producing revenue.

The International Water Association (IWA) and the World Bank estimate that over **126 billion cubic meters of treated water are lost every year**, representing an economic loss exceeding **$39 billion USD annually**. Beyond financial hemorrhage, unmanaged water loss exacerbates urban drought vulnerability, wastes enormous electrical energy expended in water treatment and pumping (contributing to carbon emissions), and introduces contamination risks when subterranean pressure drops allow contaminated groundwater ingress into depressurized drinking water mains.

---

## 2. The Core Anomaly: SIV vs. Billed Consumption

In an ideal, lossless network:
$$\text{System Input Volume (SIV)} = \sum \text{Authorized Billed Consumption} + \sum \text{Authorized Unbilled Consumption}$$

In real-world networks, this balance never closes. The difference represents water loss, which stems from three distinct root causes:

```
Total Water Input (System Input Volume - SIV)
 │
 ├── Authorized Consumption
 │    ├── Billed Metered Consumption (Domestic, Commercial, Industrial)
 │    ├── Billed Unmetered Consumption
 │    └── Unbilled Authorized (Firefighting, Main flushing, Public fountains)
 │
 └── Non-Revenue Water (NRW)
      ├── Commercial / Apparent Losses
      │    ├── Customer meter inaccuracy (meter under-registration at low flows)
      │    ├── Unauthorized consumption (theft, illegal taps)
      │    └── Data handling and billing calculation errors
      │
      └── Real / Physical Losses (Target of WATERPRINT)
           ├── Transmission main bursts (high volume, short duration)
           ├── Distribution pipe background leakage (low volume, long duration)
           ├── Service connection joint leaks (highest frequency of occurrence)
           └── Storage tank leaks and overflows
```

---

## 3. Operational Pain Points in Current Utility Practices

1. **Long Awareness and Localization Delays:**
   Utilities typically discover leaks through customer reports (e.g. water bubbling up on the street) or months later during quarterly meter reconciliation. By that time, millions of liters have been wasted, and soil erosion around the pipe foundation often leads to sinkholes and structural roadway collapse.
2. **Conflation of Sensor Glitches with Physical Leaks:**
   SCADA systems generate thousands of false alarms because transient telemetry packet loss, stuck ADC converters (flatlines), and calibration drifts trigger naive threshold alerts. Operators suffer alarm fatigue and disable alerts.
3. **Absence of Systematic Minimum Night Flow (MNF) Analysis:**
   During daytime, normal user demand variations ($\pm 25\%$) completely mask incipient leaks of 1–5 $m^3/h$. Only during nocturnal Minimum Night Flow (02:00 – 04:00 AM), when legitimate demand is minimal and network pressure is highest, can leaks be identified with high signal-to-noise ratio.
4. **False Precision in Leak Localization:**
   Many academic prototypes claim exact GPS coordinates for leaks based solely on sparse pressure sensors. In practice, multiple nodes in a topological loop exhibit identical pressure drop signatures due to hydraulic equivalence. Utilities need **probabilistically ranked candidate zones/nodes with explicit uncertainty bounds**, not overconfident false locations.

---

## 4. Objectives of WATERPRINT

WATERPRINT is an end-to-end, production-grade intelligence platform engineered to:
* **Ingest and Harmonize** heterogeneous multi-rate time-series: DMA boundary inflow, pressure transducers, smart meter consumption, and tank levels.
* **Segregate Sensor Faults from Physical Leaks** via multi-tier validation (flatline detection, physical bound enforcement, rate-of-change filters).
* **Execute Multi-Method Anomaly Detection** combining standard IWA water balance, nocturnal MNF tracking, machine learning baseline residual forecasting, Isolation Forests, and change-point detection (CUSUM).
* **Rank Candidate Network Zones** using network topology and hydraulic pressure sensitivity matrices, providing clear evidentiary justification.
* **Deliver Actionable Operational Intelligence** through an interactive executive dashboard, audit trails, and exportable engineering reports.
