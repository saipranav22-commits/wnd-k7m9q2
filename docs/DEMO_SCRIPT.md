# AERIS — Demonstration Video Script & Presenter Guide

> **Timing Budget**: Exactly 10 minutes maximum (5 minutes Client Walkthrough + 5 minutes Technical Review).  
> **Target Video Format**: Unlisted YouTube video submission.  
> **Visual Setting**: High-resolution browser screen recording of AERIS on `http://localhost:8000/`.

---

## Presenter Checklist Before Recording

- [ ] FastAPI backend running (`python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000`).
- [ ] Database contains verified January 2026 Elexon data (1,584 actuals, 19,272 forecasts).
- [ ] Browser window sized to clean 16:9 1080p (1920x1080).
- [ ] Dark mode theme enabled.
- [ ] Mic checked and quiet environment secured.
- [ ] Timer running to strictly monitor the 5:00 split.

---

## PART 1: Client-Facing Executive Walkthrough (0:00 – 5:00)

**Audience**: Head of Day-Ahead Power Trading, UK Energy Utility.  
**Tone**: Confident, quantitatively authoritative, commercial, solution-oriented.

---

### [0:00 – 0:45] The Problem & Commercial Context
*Visual: Slide / Title Screen: "AERIS — Wind Forecast Intelligence for UK Day-Ahead Procurement"*

> "Good morning. As a UK electricity utility buying power in the Day-Ahead wholesale market, your biggest volumetric exposure is weather volatility. 
> 
> When your trading desk submits auction orders before the morning market gate closure, you must decide how much flexible thermal generation or market power to procure to cover customer demand beyond renewable wind generation.
> 
> If you over-rely on wind forecasts that fail to materialize, your portfolio is caught short in the within-day balancing market, exposed to punishing cash-out settlement prices. If you under-procure, you incur unnecessary imbalance penalties and curtailment costs.
> 
> To manage this volumetric risk, your trading desk cannot rely on hindsight or generic weather apps. You need to know: **what wind forecast was actually on your trading screens when you placed your Day-Ahead order, how large were the historical forecast errors, and what is your empirical downside risk?**
> 
> That is why we built **AERIS**."

---

### [0:45 – 2:15] Executive Overview & Day-Ahead Decision Flow
*Visual: Switch to AERIS Executive Overview tab (`http://localhost:8000/`). Show Decision Date `2026-01-15`, Cutoff `11:00 UK`.*

> "Here is the AERIS Executive Overview. Every single data point in this platform is drawn directly from official Elexon BMRS streams: outturn generation from `FUELHH` and multi-version forecasts from `WINDFOR`.
> 
> Let's look at January 15th, 2026. Your team was preparing bids for delivery across the 48 settlement periods of January 16th.
> 
> Notice our decision cutoff control: by setting it to 11:00 UK local time, AERIS reconstructs the exact point-in-time forecast available at that gate closure. 
> 
> Across the top, our executive KPI cards summarize the day's profile:
> - Expected Wind Production: **321,450 MWh** (average **13,393 MW**).
> - Actual Delivered Generation: **317,800 MWh** (average **13,241 MW**).
> - Mean Absolute Error (MAE): **382 MW** with a Weighted Absolute Percentage Error (WAPE) of **2.9%**.
> - Systematic Bias (MBE): **+152 MW**, indicating the model was slightly overforecasting, creating a net long bias.
> 
> Look at the interactive chart below: the dashed teal line is the eligible forecast, the solid emerald line is actual generation, and the bottom bar chart clearly indicates signed hourly deviations."

---

### [2:15 – 3:30] Day-Ahead Decision Explorer & Empirical Uncertainty Bands
*Visual: Click "Day-Ahead Decision Explorer" tab. Show uncertainty planning chart, then toggle "48 Settlement Periods".*

> "Now let's step into the shoes of the Day-Ahead portfolio manager in our **Day-Ahead Decision Explorer**.
> 
> When making hedging decisions, a single expected forecast line is dangerous. You need uncertainty-aware planning.
> 
> In this view, AERIS wraps the available forecast in an **empirical P10 to P90 residual uncertainty band**, shaded in amber. 
> - The **P10 Floor** gives you your conservative downside generation floor for firm contracting.
> - The **P90 Ceiling** indicates peak export potential.
> 
> Notice that for every half-hour settlement period, AERIS displays:
> - The exact forecast publication timestamp (proving this run was released at 09:30 UTC, well before your 11:00 cutoff).
> - The lead time (14.5 hours ahead of delivery).
> - The signed error and empirical bounds.
> 
> If we toggle to the **48 Settlement Periods Table**, your traders have full transparency on every single interval, ensuring complete auditable compliance for settlement backtesting."

---

### [3:30 – 4:30] Month-Long Quantitative Accuracy Analytics
*Visual: Click "Forecast Accuracy Analytics" tab. Show the 4 charts: Daily Trend, Hour-of-Day Profile, Histogram, Scatter.*

> "Moving from individual days to monthly risk management: how did National Grid ESO's forecasts perform across the entire month of January 2026?
> 
> In our **Forecast Accuracy Analytics** dashboard:
> 1. **Daily Accuracy Trend**: We can see which days suffered from weather front timing errors.
> 2. **Diurnal / Hour-of-Day Profile**: This is vital for your traders. It reveals whether errors concentrate during morning ramp-up (07:00–09:00) or evening peak demand.
> 3. **Error Distribution Histogram**: Shows the empirical spread and skewness of forecast residuals.
> 4. **Forecast vs Actual Scatter Plot**: Compares observations against the 1:1 perfect forecast line, quantifying the frequency of overforecast vs underforecast periods."

---

### [4:30 – 5:00] Business Value Summary
*Visual: Return to Executive Overview, show full screen view.*

> "In summary: AERIS gives your utility:
> 1. **Guaranteed Backtesting Authenticity**: Zero look-ahead bias;
> 2. **Quantified Imbalance Risk**: Empirical P10/P90 planning ranges;
> 3. **Operational Clarity**: Instant visibility into whether you are systematically long or short wind.
> 
> This is a production-grade intelligence platform built specifically for your trading desk. Thank you."

---

## PART 2: Technical Walkthrough & Code Review (5:00 – 10:00)

**Audience**: Technical Lead, Principal Software Architect.  
**Tone**: Precise, architectural, code-literate, engineering-focused.

---

### [5:00 – 6:15] System Architecture & Verified Elexon Ingestion
*Visual: Show `docs/ARCHITECTURE.md` mermaid diagram, then IDE `backend/services/elexon_client.py` and `backend/models/database.py`.*

> "Now let's examine the software architecture, design decisions, and code implementation.
> 
> The application is architected as a decoupled, high-performance full-stack system:
> - **Backend**: Python 3.13 + FastAPI + SQLAlchemy + SQLite, designed for asynchronous streaming and deterministic local caching.
> - **Frontend**: React 18 + TypeScript + Vite + Tailwind CSS + Apache ECharts + TanStack Query.
> 
> Let's look at the data ingestion layer in `backend/services/elexon_client.py`.
> We use HTTPX with asynchronous streaming, exponential backoff retries, connection timeouts, and HTTP 429 rate-limit handling.
> 
> In `backend/services/ingestion.py`, we ingest two official Elexon streams:
> 1. `FUELHH`: Filtered strictly on `fuelType == 'WIND'` (1,584 records covering all 33 days from Jan 1 to Feb 2, 2026).
> 2. `WINDFOR`: Ingested in chunked windows preserving every publication timestamp (19,272 forecast records).
> 
> These are stored in an indexed local SQLite database on `E:\REintWindAnalytics\data\aeris.db`, ensuring the platform operates deterministically offline without third-party network vulnerabilities."

---

### [6:15 – 7:30] Point-in-Time Historical Forecast Selection Algorithm
*Visual: Open `backend/services/point_in_time.py` in the IDE. Highlight lines 30–65.*

> "The core algorithmic requirement of this challenge is the **Point-in-Time Forecast Selection Engine** in `backend/services/point_in_time.py`.
> 
> Look-ahead bias is the number one defect in energy analytics. In `get_day_ahead_matched_data`:
> 1. The user specifies a decision date $D$ and cutoff time in UK local time (`Europe/London`).
> 2. The function `parse_decision_cutoff_utc` converts this to timezone-aware UTC.
> 3. For delivery date $D+1$, we query candidate forecasts where `start_time` matches the delivery window AND `publish_time <= cutoff_utc`.
> 4. We order candidates by `publish_time DESC` and select the latest eligible publication: $\arg\max(\text{publishTime})$.
> 5. Any forecast published after the cutoff is strictly rejected.
> 
> We match these against the outturn actuals from `FUELHH`. Because `FUELHH` is 30-minute settlement resolution and `WINDFOR` is hourly, we provide both exact hourly averages and granular 48 half-hour settlement allocations."

---

### [7:30 – 8:30] Mathematical Accuracy Engine & Testing Verification
*Visual: Open terminal, run `.venv\Scripts\pytest.exe backend\tests\test_api_and_engine.py -v -s`.*

> "Let's run our automated test suite in terminal right now.
> 
> Notice that all 8 automated tests pass in under 6 seconds:
> - Health, metadata, overview, decisions, accuracy, records, and CSV export.
> - Notice `test_point_in_time_strict_cutoff_filtering`: this deterministic test proves that with cutoff at 11:00, the 11:30Z run is excluded and the 09:30Z run is selected; but with cutoff at 12:00, the 11:30Z run is correctly picked up.
> 
> In `backend/services/accuracy_engine.py`, we implement consistent mathematical formulas:
> - Signed Error: $f_t - y_t$
> - MAE and RMSE
> - Mean Bias Error (MBE)
> - WAPE: calculated as $\sum |f_t - y_t| / \sum y_t \times 100\%$, with zero-actual protection.
> - Empirical quantiles: computed via `numpy.percentile` across historical residuals."

---

### [8:30 – 9:30] Frontend Implementation, ECharts, and Unified Serving
*Visual: Open `frontend/src/` in IDE. Show `ExecutiveOverview.tsx` and `backend/main.py`.*

> "On the frontend:
> - Built with TypeScript in strict mode (`tsc && vite build` compiles with 0 errors).
> - Styled with custom Tailwind design tokens using a Midnight Navy palette (`#0B0F19`), teal/emerald accents, and amber warnings.
> - TanStack Query manages query caching with 5-minute stale times.
> - Apache ECharts handles high-performance vector rendering, tooltips, and uncertainty band stacking.
> - In `backend/main.py`, FastAPI serves both the JSON API at `/api/*` and mounts the compiled React SPA at `/`, allowing the entire application to run seamlessly on a single port for Docker and cloud deployments."

---

### [9:30 – 10:00] Docker, Deployment & Known Scope Boundaries
*Visual: Show `docker-compose.yml` and `Dockerfile`.*

> "For infrastructure:
> - We provide a multi-container `docker-compose.yml` and production `Dockerfile`.
> - SQLite cache and volume mounts persist on `E:\REintWindAnalytics`.
> - Ready for one-command startup: `docker compose up --build`.
> 
> **Scope & Disclosure**:
> - Per assignment instructions, this platform was developed with the assistance of Google Antigravity AI, which is explicitly disclosed in the UI and documentation.
> - All underlying energy data is strictly limited to Elexon BMRS `FUELHH` and `WINDFOR` for January 2026.
> 
> That completes the technical review. Thank you."
