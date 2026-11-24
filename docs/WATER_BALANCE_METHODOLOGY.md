# WATERPRINT: Water Balance Methodology & Nocturnal Minimum Night Flow (MNF)

## 1. The IWA Standard Water Balance

The International Water Association (IWA) and the American Water Works Association (AWWA) have established an internationally accepted framework for standardizing water audit accounting. The balance accounts for every cubic meter of water supplied into a distribution system or District Metered Area (DMA).

```
+-----------------------------------------------------------------------------------------+
|                                  SYSTEM INPUT VOLUME (SIV)                              |
+---------------------------------------------------+-------------------------------------+
|              AUTHORIZED CONSUMPTION               |           WATER LOSSES              |
+-------------------------+-------------------------+------------------+------------------+
|   Billed Authorized     |   Unbilled Authorized   | Apparent Losses  |   Real Losses    |
+-------------------------+-------------------------+------------------+------------------+
| • Billed Metered        | • Unbilled Metered      | • Customer meter | • Transmission   |
|   (Residential, Comm.)  |   (Municipal parks)     |   inaccuracies   |   bursts         |
| • Billed Unmetered      | • Unbilled Unmetered    | • Data handling  | • Distribution   |
|   (Flat-rate tariffs)   |   (Firefighting, mains  |   errors         |   mains leaks    |
|                         |    flushing, scours)    | • Unauthorized   | • Service pipes  |
|                         |                         |   use (theft)    | • Tank overflows |
+-------------------------+-------------------------+------------------+------------------+
|            REVENUE WATER                          |        NON-REVENUE WATER (NRW)  |
+---------------------------------------------------+-------------------------------------+
```

### Governing Balance Equations

1. **System Input Volume (SIV):**
   $$\text{SIV}(t) = \sum_{i \in \text{Inlets}} Q_i(t) - \sum_{j \in \text{Outlets}} Q_j(t) \pm \Delta V_{\text{storage}}(t)$$
   where $Q_i$ and $Q_j$ are metered boundary flows and $\Delta V_{\text{storage}}$ is the net volumetric storage rate change in balancing tanks.

2. **Non-Revenue Water (NRW):**
   $$\text{NRW} = \text{SIV} - \text{Billed Authorized Consumption}$$
   $$\text{NRW Ratio (\%)} = \left(\frac{\text{NRW}}{\text{SIV}}\right) \times 100$$

3. **Real Losses ($V_{\text{real}}$):**
   $$V_{\text{real}} = \text{SIV} - (\text{Authorized Consumption} + \text{Apparent Losses})$$

---

## 2. Minimum Night Flow (MNF) Analysis

While macro-level water balances provide monthly or annual accounting, they are incapable of detecting emergent pipe bursts in near-real-time due to customer billing latency. To overcome this, WATERPRINT implements automated **Minimum Night Flow (MNF)** analytics.

### Why Nocturnal Flow?
Between **02:00 and 04:00 AM**:
1. Legitimate human activity (showering, laundry, cooking, commercial activity) drops to its diurnal minimum.
2. Pressure in the distribution network rises to its 24-hour diurnal peak ($P_{\max}$) because frictional head losses along the pipes drop to near zero.
3. Because physical leakage is pressure-dependent ($q_{\text{leak}} \propto P^\alpha$), physical leaks discharge at their maximum rate, maximizing the signal-to-noise ratio.

```
Flow Rate (m³/h)
  ▲
  │         Diurnal Morning Peak
  │              ╭───╮
  │             ╭╯   ╰╮
  │     ╭───────╯     ╰──────╮    Evening Peak
  │    ╭╯                    ╰───╭───╮
  │   ╭╯                         │   ╰──╮
  │   │                                 ╰──╮
  │   │                                    │
  ├───┼────────────────────────────────────┼───► Time of Day
 00  02       04        08       12       18  24
     ▲────────▲
       MNF WINDOW (02:00 - 04:00)
```

### Mathematical Decomposition of MNF

$$\bar{Q}_{\text{MNF}} = Q_{\text{legitimate, night}} + Q_{\text{background}} + Q_{\text{bursts}}$$

* **$\bar{Q}_{\text{MNF}}$:** The lowest rolling 1-hour average inflow observed between 02:00 and 04:00.
* **$Q_{\text{legitimate, night}}$:** Estimated nocturnal domestic and commercial usage:
  $$Q_{\text{legitimate, night}} = N_{\text{props}} \cdot q_{\text{prop}} + Q_{\text{known commercial}}$$
  where $N_{\text{props}}$ is the number of connected properties and $q_{\text{prop}} \approx 1.5 - 2.5\text{ liters/property/hour}$ based on the Diehl Hydrus residential benchmark.
* **$Q_{\text{background}}$:** Allowable background seepage from microscopic weeping joints:
  $$Q_{\text{background}} = \beta \cdot L_{\text{mains}} \cdot P_{\text{avg}}^{1.5}$$
* **Net Night Flow (NNF):**
  $$\text{NNF} = \bar{Q}_{\text{MNF}} - Q_{\text{legitimate, night}}$$
  $$\text{Unaccounted Night Loss} = \text{NNF} - Q_{\text{background baseline}}$$

Any sustained upward deviation in NNF indicates an active, unrecorded leak.

---

## 3. Pressure-Dependent Leakage Physics (FAVAD Concept)

Traditional orifice hydraulics assumes that orifice discharge follows Torricelli's Law ($Q \propto \sqrt{h}$):
$$q = C_d A_0 \sqrt{2g h}$$

However, in buried municipal pipelines, structural cracks expand elastically under internal water pressure. May (1994) and Lambert (2001) formulated the **Fixed and Variable Area Discharges (FAVAD)** model:
$$q_{\text{leak}} = C \cdot P^{N_1}$$

* **Rigid Pipes (Cast Iron, Steel, Asbestos Cement):** Corrosion pinholes have fixed geometric area ($A = A_0$). Here $N_1 \approx 0.50$.
* **Flexible Pipes (uPVC, MDPE, HDPE):** Longitudinal splits and ring fractures flex open as pressure increases. The leak area varies with pressure ($A = A_0 + m \cdot P$). Consequently, $N_1$ ranges from **1.10 to 1.50**.
* **Implication for WATERPRINT:** A 15% nocturnal pressure surge produces up to a 25% surge in leakage discharge rate on plastic distribution mains, making pressure tracking indispensable.

---

## 4. Key Performance Indicators: CARL, UARL, and ILI

To benchmark network efficiency independently of network size and operating pressure, WATERPRINT calculates the **Infrastructure Leakage Index (ILI)**:

$$\text{ILI} = \frac{\text{Current Annual Real Losses (CARL)}}{\text{Unavoidable Annual Real Losses (UARL)}}$$

### Unavoidable Annual Real Losses (UARL)
Developed by the IWA Water Losses Task Force, UARL represents the theoretical minimum technical loss achievable in a well-maintained network:
$$\text{UARL (liters/day)} = (18 \times L_m + 0.80 \times N_c + 25 \times L_p) \times \bar{P}$$

* $L_m$: Total length of distribution mains ($km$).
* $N_c$: Number of customer service connections.
* $L_p$: Total length of private underground pipes between street curb and property meter ($km$).
* $\bar{P}$: Average operating pressure ($m$ of head).

### ILI Interpretation Standard:
* **$\text{ILI} < 1.5$ (Category A - World Class):** Outstanding leakage management; further physical loss reduction may be uneconomic.
* **$1.5 \le \text{ILI} < 4.0$ (Category B - Good):** Potential for marked improvement; targeted active leak detection recommended.
* **$4.0 \le \text{ILI} < 8.0$ (Category C - Poor):** Poor condition; substantial physical leakage; intensive pressure management and acoustic inspection required.
* **$\text{ILI} \ge 8.0$ (Category D - Critical):** Catastrophic structural inefficiency; urgent capital pipe replacement needed.

---

## 5. Failure Modes of Water Balance Analysis

1. **AMR Time Asynchrony:** Customer smart meters reporting daily or monthly cannot be directly subtracted from instantaneous 15-minute SCADA flows without disaggregation interpolation.
2. **Meter Under-Registration:** Mechanical multi-jet meters lose sensitivity below their transition flow rate ($Q_1$), falsely appearing as physical distribution losses.
3. **Storage Dynamic Buffering:** Neglecting tank volume fluctuations ($\Delta V = A_{\text{tank}} \Delta h_{\text{level}}$) creates artificial apparent inflows or losses during pump recharge cycles.
