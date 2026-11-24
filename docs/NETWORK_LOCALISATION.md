# WATERPRINT: Network-Based Leak Localisation Methodology

## 1. The Inverse Problem of Hydraulic Leak Localisation

In a municipal water distribution network spanning hundreds of kilometers of underground pipes, utilities deploy only a sparse set of pressure sensors (typically 5 to 35 sensors across an entire DMA) due to telemetry capital and maintenance costs.

When a leak occurs at node or pipe $j$, it introduces an additional sink discharge $q_{\text{leak}}$. This extra flow induces additional friction losses, resulting in a network-wide pressure drop.
The observed pressure vector at the $m$ monitored sensor nodes changes from baseline $\mathbf{P}_0 \in \mathbb{R}^m$ to $\mathbf{P}_{\text{obs}} \in \mathbb{R}^m$.

The pressure residual vector is defined as:
$$\mathbf{r}_P = \mathbf{P}_0 - \mathbf{P}_{\text{obs}} = [\Delta P_1, \Delta P_2, \dots, \Delta P_m]^T$$

The engineering challenge: **Given sparse $\mathbf{r}_P \in \mathbb{R}^m$ (where $m \ll n$, with $n$ being the total number of junctions), infer the candidate leak origin node $j \in \{1, \dots, n\}$.**

---

## 2. Why Exact Pinpoint Localisation is Mathematically Ill-Posed

> [!CAUTION]
> **Engineering Honesty Principle:** Claiming exact GPS pinpointing of a subterranean pipe burst from a few sparse SCADA pressure sensors is technically unsound and misleads field repair crews. In looped distribution networks:
> 1. Multiple adjacent junction nodes often have nearly collinear pressure sensitivity vectors due to hydraulic equivalence.
> 2. Sensor measurement noise ($\pm 0.15\text{ m}$) is comparable in magnitude to the pressure drop caused by small incipient leaks ($0.20 - 0.50\text{ m}$).
> 3. Normal customer demand fluctuations induce pressure shifts that mask the leak signature.

Therefore, WATERPRINT **strictly rejects false pinpointing** and instead delivers a **probabilistically ranked set of candidate zones and nodes** with quantified confidence scores.

---

## 3. Mathematical Methodology

### 3.1 Hydraulic Sensitivity Matrix Formulation
The steady-state relationship between nodal demands/leaks $\mathbf{q} \in \mathbb{R}^n$ and junction heads $\mathbf{H} \in \mathbb{R}^n$ is governed by the non-linear conservation of mass and Hazen-Williams energy equations:
$$\mathbf{A}_1 \mathbf{Q} + \mathbf{q} = \mathbf{0}$$
$$\mathbf{h}_f = \mathbf{A}_1^T \mathbf{H} = r |\mathbf{Q}|^{1.852-1} \mathbf{Q}$$

Linearizing around the nominal operating point yields the **Hydraulic Sensitivity Matrix** $\mathbf{S} \in \mathbb{R}^{m \times n}$:
$$S_{ij} = \frac{\partial P_i}{\partial q_j} \approx \frac{P_i(q_j + \delta q) - P_i(q_j)}{\delta q}$$
where $S_{ij}$ represents the pressure drop expected at sensor node $i$ when an extra unit outflow occurs at candidate node $j$.
Each column $\mathbf{s}_j \in \mathbb{R}^m$ represents the unique theoretical **pressure drop fingerprint** of node $j$.

### 3.2 Fingerprint Similarity Scoring
When an active leak is declared, the observed pressure residual vector $\mathbf{r}_P$ is compared against every column $\mathbf{s}_j$ of the sensitivity matrix using correlation and normalized projection:

1. **Pearson Correlation Metric:**
   $$\rho_j = \frac{(\mathbf{r}_P - \bar{r}_P)^T (\mathbf{s}_j - \bar{s}_j)}{\|\mathbf{r}_P - \bar{r}_P\|_2 \, \|\mathbf{s}_j - \bar{s}_j\|_2}$$

2. **Cosine Angle Metric:**
   $$\cos(\theta_j) = \frac{\mathbf{r}_P^T \mathbf{s}_j}{\|\mathbf{r}_P\|_2 \, \|\mathbf{s}_j\|_2}$$

3. **Combined Likelihood Score:**
   $$\mathcal{L}(j) = \max\left(0, \, \alpha \cdot \rho_j + (1 - \alpha) \cdot \cos(\theta_j)\right)$$

### 3.3 Graph Topological Distance Weighting
Hydraulic pressure signals propagate along pipes according to hydraulic impedance. Using **NetworkX**, WATERPRINT computes the shortest hydraulic distance path $d_{\text{hyd}}(i, j)$ across the pipe graph:
$$w_{\text{edge}}(u, v) = \frac{10.67 \cdot L_{uv}}{C_{uv}^{1.852} \cdot D_{uv}^{4.87}}$$

Nodes that are hydraulically upstream or closer to the sensors exhibiting the largest pressure anomalies receive Bayesian spatial prior boosting:
$$P(j \mid \mathbf{r}_P) \propto \mathcal{L}(j) \cdot \exp\left( - \lambda \min_{k \in \text{Sensors}} \frac{d_{\text{hyd}}(j, k)}{\bar{d}} \right)$$

### 3.4 Candidate Zone Clustering & Ranking
Candidate nodes are ranked by posterior probability $P(j \mid \mathbf{r}_P)$:
$$\text{Ranked List} = \text{SortDescending}\left(\{ (j, P(j \mid \mathbf{r}_P)) \}_{j=1}^n\right)$$
The nodes are aggregated by their topological sub-zone (e.g. `ZONE_NORTH_EAST`, `ZONE_SOUTH_WEST`), returning the **Top-$k$ candidate search zones** with aggregated confidence percentages (e.g. Zone A: 64%, Zone B: 24%, Zone C: 12%).

---

## 4. Failure Modes and Limitations

1. **Symmetric Looped Networks:** In perfectly balanced grid layouts, a leak halfway between two parallel mains can produce identical pressure drops at boundary sensors, creating a bimodal candidate distribution.
2. **Pressure Reducing Valve (PRV) Dynamics:** Active PRVs dynamically throttle head loss to maintain constant downstream pressure. This non-linear control action absorbs pressure waves and can decouple upstream pressure signatures from downstream leaks.
3. **Low Velocity Regimes:** In oversized pipes ($D > 300\text{ mm}$) with slow velocities ($v < 0.3\text{ m/s}$), small leaks ($< 2\text{ m}^3\text{/h}$) generate head losses of mere millimeters, which fall beneath the noise floor of standard field pressure transducers.
