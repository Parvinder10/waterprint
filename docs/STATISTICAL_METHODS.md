# WATERPRINT: Statistical and Machine Learning Methods

## 1. Overview of Analytical Methods

WATERPRINT employs a defense-in-depth analytical pipeline combining statistical hypothesis testing, parametric and non-parametric time-series forecasting, unsupervised machine learning, and sequential change-point detection.

---

## 2. Baseline Flow Forecasting Engine

### 2.1 Formulation
A pipe leak manifests as an unexpected, sustained positive residual between actual observed inlet flow $Q(t)$ and the normal consumer demand $\hat{Q}(t)$ that *would have occurred* under uncompromised network conditions:
$$r_Q(t) = Q_{\text{observed}}(t) - \hat{Q}_{\text{expected}}(t)$$

### 2.2 Feature Representation
The feature vector $\mathbf{x}_t \in \mathbb{R}^d$ includes:
* **Harmonic Trigonometric Encodings (Diurnal & Weekly cycles):**
  $$\phi_{\text{day}, 1} = \sin\left(\frac{2\pi \cdot \text{hour}}{24}\right), \quad \phi_{\text{day}, 2} = \cos\left(\frac{2\pi \cdot \text{hour}}{24}\right)$$
  $$\phi_{\text{week}, 1} = \sin\left(\frac{2\pi \cdot \text{dow}}{7}\right), \quad \phi_{\text{week}, 2} = \cos\left(\frac{2\pi \cdot \text{dow}}{7}\right)$$
* **Autoregressive Lags:** $Q(t - 1\text{ step})$, $Q(t - 4\text{ steps})$ (1 hour), $Q(t - 96\text{ steps})$ (24 hours), $Q(t - 672\text{ steps})$ (1 week).
* **Rolling Demand Statistics:** Rolling 3-hour mean, rolling 24-hour standard deviation.
* **Operational Regimes:** Pump speed, inlet valve throttling status.

### 2.3 Learning Algorithms
1. **Quantile Gradient Boosting (Primary Default):**
   Trained with pinball loss $L_\tau(y, \hat{y}) = \max(\tau(y - \hat{y}), (1 - \tau)(\hat{y} - y))$ for quantiles $\tau \in \{0.025, 0.50, 0.975\}$.
   * Provides non-linear feature interactions without normality assumptions.
   * Directly yields the conditional median $\hat{Q}_{0.50}(t)$ and asymmetric $95\%$ empirical prediction intervals $[\hat{Q}_{0.025}(t), \hat{Q}_{0.975}(t)]$.
2. **Regularized Ridge Fourier Regression (Fast Linear Baseline):**
   $$\min_{\mathbf{w}} \|\mathbf{y} - \mathbf{X}\mathbf{w}\|_2^2 + \lambda \|\mathbf{w}\|_2^2$$
   Provides deterministic, ultra-fast calibration suitable for embedded RTUs.

---

## 3. Residual-Based Anomaly Detection

### 3.1 Standardized Residual Score
Given the baseline estimate $\hat{Q}(t)$ and historical standard deviation of residuals $\sigma_r$, the standardized residual is:
$$z_r(t) = \frac{Q(t) - \hat{Q}(t)}{\sigma_r}$$

### 3.2 Dynamic Uncertainty Bounds & Bayesian Formulation
Under a Gaussian-process or Bayesian linear formulation with observation noise $\sigma^2$ and parameter covariance $\boldsymbol{\Sigma}_w$:
$$\hat{Q}(t) \sim \mathcal{N}\left(\mathbf{x}_t^T \boldsymbol{\mu}_w, \, \sigma^2 + \mathbf{x}_t^T \boldsymbol{\Sigma}_w \mathbf{x}_t\right)$$
* **Epistemic Uncertainty ($\mathbf{x}_t^T \boldsymbol{\Sigma}_w \mathbf{x}_t$):** High during rare holidays or weather anomalies where training data is scarce.
* **Aleatoric Uncertainty ($\sigma^2$):** Baseline consumer usage variability.
* **Decision Rule:** An observation is flagged anomalous if:
  $$Q(t) > \hat{Q}_{0.975}(t) + k \cdot \sigma_{\text{epistemic}}(t)$$

---

## 4. Sequential Change-Point Detection (CUSUM)

A slow pipe leak often causes a small step increase in inflow ($+3\text{ to }+8\%$) that falls within the normal diurnal variance of a single time step. Point anomaly filters miss this. Sequential Cumulative Sum (CUSUM) accumulates small, consistent positive drifts:

### 4.1 Tabular CUSUM Algorithm
$$S_0^+ = 0$$
$$S_t^+ = \max\left(0, \, S_{t-1}^t + z_r(t) - k_{\text{drift}}\right)$$

* $k_{\text{drift}} = \frac{\delta}{2}$: Reference drift parameter (typically $0.50\sigma$), defining the minimum shift size detectable.
* $h_{\text{thresh}}$: Decision boundary (typically $4.50\sigma$).
* **Alarm Trigger:** If $S_t^+ > h_{\text{thresh}}$, an abrupt or persistent change-point is declared at timestamp $t^* = \arg\max_{\tau < t} (S_\tau^+ = 0)$.

---

## 5. Unsupervised Multivariate Isolation Forest

### 5.1 Formulation
While flow residuals highlight volumetric loss, pressure drops confirm physical burst dynamics. We construct a multi-dimensional state space:
$$\mathbf{u}_t = \left[ r_Q(t), \; \frac{dr_Q}{dt}, \; \Delta \bar{P}(t), \; r_{\text{MNF}}(t) \right]^T$$

* An ensemble of $T = 150$ randomized isolation trees recursively splits features.
* The anomaly score $s(\mathbf{u}, n)$ is computed as:
  $$s(\mathbf{u}, n) = 2^{-\frac{\mathbb{E}[h(\mathbf{u})]}{c(n)}}$$
  where $h(\mathbf{u})$ is path length to isolation and $c(n) = 2\ln(n - 1) + 0.5772 - \frac{2(n - 1)}{n}$.
* Contamination parameter calibrated to $\gamma = 0.035$ based on utility operating standards.

---

## 6. Persistence Filtering & Alarm Fusion

Single-interval spikes are frequently caused by transient hydraulic surges (e.g. pump start, valve throttling) or sensor telemetry noise.
To eliminate transient false alarms:
1. **Persistence Filter:** An alarm is promoted from `SUSPECT` to `CONFIRMED_LEAK` only if the anomaly condition persists for $m \ge 3$ consecutive periods (45 minutes).
2. **Multi-Sensor Coincidence:** A volumetric flow anomaly is cross-checked against nodal pressure residuals ($\Delta P < -\theta_P$). If flow increases without any localized pressure drop, the event is tagged as a potential legitimate unmetered demand spike rather than a physical burst.

---

## 7. Assumptions & Failure Modes

| Method | Key Assumptions | Failure Mode / Vulnerability | Mitigation in WATERPRINT |
| :--- | :--- | :--- | :--- |
| **Baseline Forecasting** | Consumer demand follows recurrent diurnal/weekly periodicity. | Major public holidays, sporting events, or pandemic lockdowns alter diurnal routines. | Holiday calendar flags and wide epistemic uncertainty intervals during abnormal dates. |
| **CUSUM Change-Point** | Residual errors are independent identically distributed (i.i.d.). | Strong autocorrelation in residual errors can cause false accumulation drift. | Pre-whitening residuals using AR(1) filtering before CUSUM accumulation. |
| **Isolation Forest** | Anomalies are few and topologically isolated in feature space. | Extended multi-week leaks contaminate the training window if retraining occurs during active leaks. | Strict chronological train/test isolation; historical training on certified leak-free baseline periods. |
| **Z-Score Filtering** | Underlying residual distribution is roughly Gaussian. | Heavy-tailed commercial industrial pulses trigger false positive spikes. | Median / IQR robust scaling and consecutive persistence gating ($m \ge 3$). |
