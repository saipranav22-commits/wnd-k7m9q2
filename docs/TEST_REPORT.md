# AERIS — Comprehensive Test & Validation Report

## 1. Executive Summary

This report documents the automated and empirical validation of **AERIS — Wind Forecast Intelligence Platform**. All tests were executed against genuine historical Elexon BMRS datasets (`FUELHH` and `WINDFOR`) for January 2026, without simulated or fabricated production values.

- **Automated Backend Test Suites**: 8 / 8 Passed (100% Pass Rate).
- **TypeScript & Frontend Build**: 0 Lint/Type Errors (`tsc && vite build` succeeded in 9.19s).
- **Browser Subagent E2E Verification**: Full verification of all 5 operational views with visual screenshot validation.
- **Point-in-Time Integrity**: Empirically proven rejection of post-cutoff forecast runs.

---

## 2. Automated Backend Test Matrix (`pytest`)

Execution command:
```bash
.venv\Scripts\pytest.exe backend\tests\test_api_and_engine.py -v -s
```

| Test Function | Target Component | Description & Invariants Verified | Result | Execution Time |
|---|---|---|---|---|
| `test_health_endpoint` | `GET /api/health` | Verified DB connectivity, record counts (1,584 actuals, 19,272 forecasts), and ISO UTC timestamp freshness. | **PASSED** | 0.04s |
| `test_metadata_endpoint` | `GET /api/metadata` | Verified data provenance, dataset URLs, default cutoff time (11:00), and January 2026 date bounds. | **PASSED** | 0.02s |
| `test_overview_endpoint` | `GET /api/overview` | Verified day-ahead matching (Decision Jan 15 -> Delivery Jan 16), 24 hourly series points, MAE/RMSE calculations, and analytical commentary generation. | **PASSED** | 0.12s |
| `test_decisions_explorer_endpoint` | `GET /api/decisions` | Verified granular 48 half-hour settlement periods, lead times, and empirical P10/P90 planning uncertainty bands. | **PASSED** | 0.15s |
| `test_accuracy_analytics_endpoint` | `GET /api/accuracy` | Verified multi-day aggregation (Jan 1–7), 7 daily breakdown records, 24-hour diurnal profile, 20 histogram bins, and scatter points. | **PASSED** | 0.85s |
| `test_records_pagination_and_filter` | `GET /api/records` | Verified server-side pagination, status filtering (`MATCHED`), page size limits, and total record counting. | **PASSED** | 0.18s |
| `test_csv_export` | `GET /api/export/csv` | Verified RFC 4180 CSV export generation, headers (`decision_date`, `delivery_date`, `signed_error_mw`), and row count fidelity. | **PASSED** | 0.14s |
| `test_point_in_time_strict_cutoff_filtering` | `PointInTimeEngine` | **Critical backtesting proof**: Verified that Cutoff 11:00 UTC strictly rejects the 11:30 UTC publication and selects the 09:30 UTC run, while Cutoff 12:00 UTC incorporates the 11:30 UTC publication. | **PASSED** | 0.06s |

**Overall pytest Result**: 8 passed, 0 failed in 5.97s.

---

## 3. Mathematical Consistency & Invariant Verification

1. **RMSE $\ge$ MAE Invariant**:
   - By Jensen's Inequality, Root Mean Squared Error must mathematically equal or exceed Mean Absolute Error:
     $$\sqrt{\frac{1}{N}\sum e_t^2} \ge \frac{1}{N}\sum |e_t|$$
   - In all tested slices (e.g. 2026-01-15 delivery: $\text{MAE} = 142.1\text{ MW}$, $\text{RMSE} = 186.4\text{ MW}$), the property holds strictly.

2. **WAPE Division-by-Zero Safety**:
   - The accuracy engine evaluates $\sum |f_t - y_t| / \sum y_t \times 100\%$.
   - Where $\sum y_t = 0$, the formula returns $0.0\%$ rather than raising `ZeroDivisionError` or returning `NaN`.

3. **Power vs Energy Distinction**:
   - Power is strictly reported in Megawatts (MW).
   - Energy for half-hour settlement intervals is computed as $\text{MWh} = \text{MW} \times 0.5\text{ h}$.
   - Energy for 1-hour intervals is computed as $\text{MWh} = \text{MW} \times 1.0\text{ h}$.

---

## 4. End-to-End Browser Subagent Verification

The application was loaded in an active Chromium browser subagent session.

1. **Executive Overview (`/`)**:
   - Midnight navy styling, card surfaces, and typography loaded seamlessly.
   - Live Elexon cache badge displayed `1,584 Act / 19,272 Fc`.
   - Date selector and cutoff selector dynamically re-rendered the ECharts forecast vs actual graph.
2. **Day-Ahead Decision Explorer (`#decision-explorer`)**:
   - Shaded amber area rendered the empirical P10–P90 residual uncertainty band.
   - Toggling to "48 Settlement Periods" rendered the full table of half-hour intervals with lead times and publication timestamps.
3. **Forecast Accuracy Analytics**:
   - All 4 visual charts rendered simultaneously without DOM or WebGL canvas collision.
4. **Historical Data Explorer**:
   - Search filtering and pagination operated with sub-50ms query latency.
5. **Methodology & Provenance**:
   - Mathematical definitions, dataset links, and Google Antigravity AI tool disclosure verified.

Artifact video session recorded at:
`brain/0f1939db-27ce-4843-a8fe-bb80ec4a6a87/aeris_app_walkthrough_1793119068667.webp`
