# AERIS — Data Methodology & Quantitative Specification

## 1. Underlying Energy Datasets

AERIS restricts its data sources strictly to the two official Elexon Balancing Mechanism Reporting Service (BMRS) open datasets specified in the requirements:

### 1.1 Outturn Actual Generation: `FUELHH`
- **Official Documentation**: `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream`
- **Stream Base URL**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELHH/stream`
- **Target Filter**: `fuelType = 'WIND'`
- **Temporal Resolution**: Half-hourly (30 minutes per settlement period, 48 periods per settlement day).
- **Physical Unit**: Average active power generation in Megawatts (MW) over the half-hour settlement interval.
- **Energy Conversion**: For each half-hour interval $t$, the electrical energy generated is:
  $$\text{Energy}_t \text{ [MWh]} = \text{Power}_t \text{ [MW]} \times 0.5 \text{ hours}$$
- **Key Fields**:
  - `startTime`: ISO 8601 UTC timestamp of interval commencement (e.g., `2026-01-01T00:00:00Z`).
  - `settlementDate`: Calendar date of settlement (`YYYY-MM-DD`).
  - `settlementPeriod`: Integer from 1 to 48.
  - `generation`: Average outturn generation in MW.

### 1.2 Forecast Generation: `WINDFOR`
- **Official Documentation**: `https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream`
- **Stream Base URL**: `https://data.elexon.co.uk/bmrs/api/v1/datasets/WINDFOR/stream`
- **Temporal Resolution**: Hourly intervals (commencing at `HH:00:00Z`).
- **Publication Frequency**: National Grid ESO generates and publishes updated wind forecasts approximately 8 times per day (standard update slots around 02:30, 04:30, 07:30, 09:30, 11:30, 15:30, 18:30, 22:30 UTC).
- **Physical Unit**: Forecasted wind power generation in Megawatts (MW).
- **Key Fields**:
  - `publishTime`: Timestamp when the forecast model output was created and published to market participants.
  - `startTime`: Target delivery time for the forecast interval.
  - `generation`: Forecasted wind generation in MW.

---

## 2. Temporal & Resolution Alignment

Because `FUELHH` provides half-hourly data (48 periods/day) while `WINDFOR` forecasts are issued at hourly resolution (24 points/day), a disciplined resolution alignment protocol is required:

1. **Hourly Block Mapping (Primary Analytics)**:
   - An hourly forecast with start time $H\text{:00}$ covers the 60-minute interval $[H\text{:00}, (H+1)\text{:00})$.
   - This corresponds to two consecutive half-hour settlement periods: period $2H+1$ ($H\text{:00}$) and period $2H+2$ ($H\text{:30}$).
   - The corresponding actual generation for the hour is the arithmetic mean of the two half-hourly outturn readings:
     $$\text{Actual}_{\text{hour } H} = \frac{\text{Actual}_{H:00} + \text{Actual}_{H:30}}{2}$$
   - Energy over the hour equals:
     $$\text{Energy}_{\text{hour } H} \text{ [MWh]} = \text{Actual}_{\text{hour } H} \text{ [MW]} \times 1.0 \text{ h} = 0.5 \times \text{Actual}_{H:00} + 0.5 \times \text{Actual}_{H:30}$$

2. **Half-Hourly Step Allocation (Granular Settlement View)**:
   - In the granular settlement period view, the hourly forecast value is assigned to both half-hour periods ($H\text{:00}$ and $H\text{:30}$) as the piecewise-constant expectation available for each half-hour.
   - Both representations are supported in the API: the endpoint provides granular settlement period records as well as aggregated hourly summaries.

---

## 3. Point-in-Time Historical Forecast Selection

The primary analytical failure in energy backtesting is look-ahead bias (using a forecast published at 16:00 to evaluate a trade executed at 11:00). AERIS eliminates this through rigorous point-in-time filtering:

$$\mathcal{F}_{\text{eligible}}(D, t_{\text{cutoff}}, s) = \left\{ f \in \text{WINDFOR} \;\middle|\; f.\text{startTime} = s \;\land\; f.\text{publishTime} \le \text{cutoff}(D, t_{\text{cutoff}}) \right\}$$

Where:
- $D$ is the decision date (e.g., `2026-01-15`).
- $t_{\text{cutoff}}$ is the local decision time (e.g., `11:00 Europe/London`).
- $s$ is the delivery interval start time on $D+1$ (e.g., `2026-01-16T14:00:00Z`).
- The chosen forecast is the most recent publication prior to cutoff:
  $$f^*(s) = \arg\max_{f \in \mathcal{F}_{\text{eligible}}} (f.\text{publishTime})$$

### Boundary Rules:
- **Strict Exclusion**: Any forecast with $f.\text{publishTime} > \text{cutoff}$ is strictly rejected.
- **Unmatched / Missing Flags**: If $\mathcal{F}_{\text{eligible}} = \emptyset$ for an interval, the interval is recorded as `NO_ELIGIBLE_FORECAST`. AERIS never fills missing historical forecasts with subsequent publications.
- **January 31 Decision / February 1 Delivery**: Purchasing decisions made on January 31, 2026 target power delivery on February 1, 2026. Data ingestion explicitly covers up to February 2, 2026 outturn actuals to guarantee full analytical coverage.

---

## 4. Mathematical Definitions of Metrics

Let $N$ be the number of matched intervals where both an eligible forecast $f_t$ and actual outturn $y_t$ are present.

### 4.1 Forecast Error
$$e_t = f_t - y_t \quad \text{[MW]}$$
- $e_t > 0$: **Overforecast** (utility was over-hedged / long wind).
- $e_t < 0$: **Underforecast** (utility was under-hedged / short wind, requiring spot market purchases).

### 4.2 Mean Absolute Error (MAE)
$$\text{MAE} = \frac{1}{N} \sum_{t=1}^N |f_t - y_t| \quad \text{[MW]}$$
Measures the average magnitude of volumetric forecast errors regardless of direction.

### 4.3 Root Mean Squared Error (RMSE)
$$\text{RMSE} = \sqrt{\frac{1}{N} \sum_{t=1}^N (f_t - y_t)^2} \quad \text{[MW]}$$
Penalizes large deviations disproportionately, serving as a proxy for volumetric imbalance risk in peak pricing regimes.

### 4.4 Mean Bias Error (MBE / Bias)
$$\text{MBE} = \frac{1}{N} \sum_{t=1}^N (f_t - y_t) \quad \text{[MW]}$$
Identifies systematic structural bias in the forecasting model:
- $\text{MBE} > 0$: Persistent overforecasting tendency.
- $\text{MBE} < 0$: Persistent underforecasting tendency.

### 4.5 Weighted Absolute Percentage Error (WAPE)
$$\text{WAPE} = \frac{\sum_{t=1}^N |f_t - y_t|}{\sum_{t=1}^N y_t} \times 100\%$$
Unlike Mean Absolute Percentage Error (MAPE), WAPE does not divide by individual interval actuals, completely avoiding division-by-zero or extreme percentage distortion during low-wind or curtailment periods.

### 4.6 Empirical Error Quantiles
For historical error residuals $\{e_1, e_2, \dots, e_N\}$ sorted in ascending order:
- $Q_{10}, Q_{25}, Q_{50} (\text{Median}), Q_{75}, Q_{90}$.
- These provide the empirical uncertainty bounds for wind procurement planning.
- **Disclosure**: These are empirical sample percentiles of historical deviations; they do not claim Gaussian parametric calibration or formal Bayesian posterior distribution.
