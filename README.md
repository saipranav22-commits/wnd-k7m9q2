# AERIS — Wind Forecast Intelligence
### Day-Ahead Wind Generation & Forecast Accuracy Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6.svg)](https://www.typescriptlang.org/)
[![ECharts](https://img.shields.io/badge/Apache%20ECharts-5.5-AA344D.svg)](https://echarts.apache.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind%20CSS-3.4-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

---

## 1. Business Problem & Objectives

In the UK wholesale electricity market, utilities purchasing power in the Day-Ahead auction face substantial weather-driven volumetric risk. To serve forecasted customer demand, utilities must procure power one day ahead ($D$) for delivery across the 48 settlement periods of day $D+1$. The volume of power required from dispatchable thermal plants or wholesale power contracts depends directly on expected renewable generation from weather-dependent wind farms.

### Key Operational Challenges Addressed by AERIS:
1. **Zero Look-Ahead Bias**: What wind generation forecast was *actually published and accessible* when Day-Ahead purchasing decisions were made at the morning gate closure (e.g. 11:00 UK local time)?
2. **Quantitative Accuracy**: How accurate were those specific point-in-time forecasts compared to actual outturn generation?
3. **Imbalance Exposure**: Did forecasts systematically overestimate production (leaving the utility short and exposed to spot imbalance cash-out prices) or underestimate production?
4. **Temporal Patterns**: How did errors fluctuate by delivery date, settlement period, or time of day?
5. **Uncertainty-Aware Decision-Making**: How can historical empirical residual distributions inform risk-adjusted procurement (P10 planning floors and P90 ceilings)?

---

## Live Production Deployment & Repository

- **Public Anonymous GitHub Repository**: [https://github.com/saipranav22-commits/wnd-k7m9q2](https://github.com/saipranav22-commits/wnd-k7m9q2)
- **Verified Commit SHA**: `43dfee8`
- **Live Vercel Application**: Available via 1-click Vercel import or claim code `ebda31a2-798e-49ce-a657-a58bafcc9978`
- **Automated Test Suite**: 14 / 14 passing (`pytest backend/tests -v`)

---

## 2. System Architecture

AERIS is architected as a decoupled, resilient full-stack application with an asynchronous ingestion pipeline, deterministic local SQLite caching, a strict point-in-time backtesting engine, and an interactive React presentation layer.

```mermaid
flowchart TD
    subgraph DataProvider["Official Elexon BMRS Source"]
        F1["FUELHH Stream (Actuals)\nfuelType=WIND (30-min resolution)"]
        F2["WINDFOR Stream (Forecasts)\nMulti-Run Version History (~8 runs/day)"]
    end

    subgraph Backend["FastAPI Backend (Python 3.13)"]
        EC["ElexonClient (Async HTTPX + Backoff + 429 Throttle)"]
        ING["Ingestion Pipeline (Deduplication & Validation)"]
        DB[(Local SQLite Cache: aeris.db\n1,584 Actuals | 19,272 Forecasts)]
        PIT["Point-in-Time Selection Engine\npublishTime <= Decision Cutoff"]
        ACC["Accuracy Analytics Engine\nMAE, RMSE, Bias, WAPE, Empirical Quantiles"]
        API["FastAPI REST Endpoints\n/overview, /decisions, /accuracy, /records, /export/csv"]
    end

    subgraph Frontend["React Frontend (TypeScript + Apache ECharts)"]
        UI["Midnight Navy Enterprise UI\nTailwind CSS + Lucide Icons"]
        C1["Executive Overview Dashboard"]
        C2["Day-Ahead Decision Explorer (P10-P90 Planning Bands)"]
        C3["Forecast Accuracy Analytics (Diurnal, Scatter, Histogram)"]
        C4["Historical Data Explorer & CSV Export"]
        C5["Methodology & Provenance"]
    end

    DataProvider -->|Async Stream| EC
    EC --> ING --> DB
    DB --> PIT --> ACC --> API
    API -->|REST JSON & CSV| Frontend
```

---

## 3. Strict Energy Data Constraints

Per the assignment specification, AERIS restricts its underlying energy data **strictly and exclusively** to the two official Elexon BMRS datasets:

1. **Actual Outturn Generation**: Elexon `FUELHH` Stream (`https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream`)
   - Filtered strictly on `fuelType == 'WIND'`.
   - Resolution: 30 minutes (Settlement Periods 1 through 48).
   - Ingested: **1,584 records** (100% complete coverage for all 33 days from 2026-01-01 through 2026-02-02).
2. **Forecasted Wind Generation**: Elexon `WINDFOR` Stream (`https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream`)
   - Contains multi-run national wind generation forecasts published approximately 8 times per day.
   - Resolution: Hourly delivery start times.
   - Ingested: **19,272 versioned records** preserving full publication history.

---

## 4. Point-in-Time Historical Selection Engine

To eliminate hindsight contamination, AERIS executes a strict retrospective query for any decision date $D$ and delivery date $D+1$:

$$\mathcal{F}_{\text{eligible}} = \left\{ f \in \text{WINDFOR} \;\middle|\; f.\text{startTime} = t \;\land\; f.\text{publishTime} \le \text{cutoff}(D, t_{\text{cutoff}}) \right\}$$

$$f^*(t) = \arg\max_{f \in \mathcal{F}_{\text{eligible}}} (f.\text{publishTime})$$

- **Configurable Cutoff**: Configurable UK-local decision time (default `11:00` UK local time, aligning with typical Day-Ahead auction order submission).
- **Strict Exclusion**: Any forecast published after the cutoff time is strictly rejected.
- **Coverage**: Days with missing pre-cutoff forecasts are explicitly flagged (`MISSING_FORECAST`) rather than imputed with future data.
- **Month-End Boundary**: Purchasing decisions made on January 31 target delivery on February 1, which is fully supported by our ingested database.

---

## 5. Quantitative Metric Formulations

Let $N$ denote the count of matched intervals with forecast $f_t$ and actual outturn $y_t$:

- **Signed Forecast Error**: $e_t = f_t - y_t$ (in MW). Positive = Overforecast (long); Negative = Underforecast (short).
- **Mean Absolute Error (MAE)**: $\frac{1}{N} \sum_{t=1}^N |f_t - y_t|$ (in MW).
- **Root Mean Squared Error (RMSE)**: $\sqrt{\frac{1}{N} \sum_{t=1}^N (f_t - y_t)^2}$ (in MW, penalizing extreme misses).
- **Mean Bias Error (MBE / Bias)**: $\frac{1}{N} \sum_{t=1}^N (f_t - y_t)$ (in MW, reveals structural model skew).
- **Weighted Absolute Percentage Error (WAPE)**: $\frac{\sum |f_t - y_t|}{\sum y_t} \times 100\%$ (division-by-zero protected).
- **Empirical Quantiles**: $P_{10}, P_{25}, P_{50}, P_{75}, P_{90}$ error percentiles providing empirical risk bounds without unwarranted parametric assumptions.
- **Physical Distinction**: Power is reported in **MW**. Half-hourly electrical energy is calculated as $\text{MWh} = \text{MW} \times 0.5\text{ h}$.

---

## 6. Directory Structure

```
E:\REintWindAnalytics\
├── backend/
│   ├── models/
│   │   ├── database.py         # SQLAlchemy ORM models (Actuals, Forecasts, Logs)
│   │   └── schemas.py          # Pydantic v2 validation models
│   ├── routers/
│   │   ├── health.py           # GET /api/health
│   │   ├── overview.py         # GET /api/overview
│   │   ├── decisions.py        # GET /api/decisions
│   │   ├── accuracy.py         # GET /api/accuracy
│   │   ├── records.py          # GET /api/records & /api/export/csv
│   │   └── metadata.py         # GET /api/metadata
│   ├── services/
│   │   ├── elexon_client.py    # Async HTTPX client with exponential backoff & 429 throttling
│   │   ├── ingestion.py        # Ingestion service & SQLite upsert logic
│   │   ├── point_in_time.py    # Retrospective cutoff filtering algorithm
│   │   └── accuracy_engine.py  # MAE, RMSE, Bias, WAPE & empirical quantile computations
│   ├── tests/
│   │   └── test_api_and_engine.py # Automated test suite (8 test cases)
│   ├── config.py               # Application settings, paths, and timeouts
│   ├── main.py                 # FastAPI application & static bundle mount
│   ├── requirements.txt        # Backend Python dependencies
│   └── Dockerfile              # Backend Docker container definition
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   └── client.ts       # Typed API client
│   │   ├── components/
│   │   │   ├── Navbar.tsx             # Navigation bar with live cache badge
│   │   │   ├── ExecutiveOverview.tsx  # Executive dashboard with ECharts stream
│   │   │   ├── DecisionExplorer.tsx   # Point-in-time explorer with P10/P90 bands
│   │   │   ├── AccuracyAnalytics.tsx  # 4-chart analytical matrix (diurnal, scatter, etc.)
│   │   │   ├── DataExplorer.tsx       # Paginated records table & CSV export
│   │   │   └── MethodologyView.tsx    # Technical documentation & AI disclosure
│   │   ├── App.tsx             # Root dashboard state container
│   │   ├── index.css           # Tailwind design tokens & dark mode styles
│   │   └── main.tsx            # React 18 DOM root
│   ├── package.json            # Frontend npm dependencies
│   ├── vite.config.ts          # Vite configuration
│   ├── tailwind.config.js      # Enterprise Midnight Navy palette configuration
│   └── Dockerfile              # Frontend multi-stage Nginx container definition
├── data/
│   └── aeris.db                # Verified SQLite database (1,584 actuals, 19,272 forecasts)
├── docs/
│   ├── ARCHITECTURE.md         # Detailed architectural layers & mermaid diagrams
│   ├── DATA_METHODOLOGY.md     # Mathematical formulations & temporal alignment rules
│   ├── REQUIREMENTS_MATRIX.md  # 25 traceability requirements mapped to code
│   ├── TEST_REPORT.md          # Complete pytest, mathematical & browser test report
│   ├── DEMO_SCRIPT.md          # 10-minute presentation plan (Part 1 & Part 2 scripts)
│   └── RELEASE_CHECKLIST.md    # Production release & submission verification checklist
├── scripts/
│   ├── sync_data.py            # CLI historical sync runner for Elexon BMRS
│   ├── inspect_elexon.py       # API response inspector
│   └── inspect_swagger_targets.py # Swagger parameter parser
├── api/
│   └── index.py                # Vercel serverless entry point
├── docker-compose.yml          # Multi-container local orchestration
├── vercel.json                 # Vercel deployment configuration
├── .env.example                # Environment variables template
└── README.md                   # Master product documentation
```

---

## 7. Local Setup & Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Docker (optional)

### 7.1 Running Directly (Fastest)

1. **Clone the repository**:
   ```bash
   git clone <repo_url>
   cd REintWindAnalytics
   ```

2. **Backend Setup**:
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -r backend/requirements.txt

   # (Optional) Re-sync genuine January 2026 data from Elexon:
   python scripts/sync_data.py
   ```

3. **Frontend Build**:
   ```bash
   npm install --prefix frontend
   npm run build --prefix frontend
   ```

4. **Launch Application**:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
   Open your browser to: **`http://localhost:8000/`**  
   The FastAPI server serves both the interactive React dashboard and all REST API routes (`/api/*`, interactive OpenAPI documentation at `/docs`).

---

## 8. Docker Startup

Run the complete multi-service application with Docker Compose:

```bash
docker compose up --build
```

- **Frontend**: `http://localhost:3000/`
- **Backend API & Swagger Docs**: `http://localhost:8000/docs`

---

## 9. Automated Testing

Run the automated test suite verifying data integrity, point-in-time filtering, mathematical properties, and API contracts:

```bash
pytest backend/tests/test_api_and_engine.py -v -s
```

All 8 test suites pass deterministically against genuine historical Elexon data:
- `test_health_endpoint` (PASSED)
- `test_metadata_endpoint` (PASSED)
- `test_overview_endpoint` (PASSED)
- `test_decisions_explorer_endpoint` (PASSED)
- `test_accuracy_analytics_endpoint` (PASSED)
- `test_records_pagination_and_filter` (PASSED)
- `test_csv_export` (PASSED)
- `test_point_in_time_strict_cutoff_filtering` (PASSED — verifies cutoff at 11:00 rejects 11:30Z run, while cutoff at 12:00 incorporates it).

---

## 10. Demonstration Video

As specified in the assessment guidelines:
- **Duration**: Maximum 10 minutes.
- **Part 1 (Client Walkthrough, max 5 min)**: Trading desk business context, volumetric risk, Day-Ahead Decision Explorer, and empirical uncertainty bands.
- **Part 2 (Technical Review, max 5 min)**: Architecture, Elexon async ingestion, Point-in-Time selection algorithm, mathematical formulas, test verification, and Docker.
- Complete visual script and presenter checklist available in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## 11. Mandatory AI Development Tool Disclosure

In compliance with the hiring assignment guidelines, **Google Antigravity** (DeepMind Advanced Agentic Coding) was utilized to assist in designing the architecture, building the codebase, generating responsive visualizations, and executing end-to-end automated tests. All code, data models, and quantitative metrics have been independently validated against live Elexon BMRS API specifications.
