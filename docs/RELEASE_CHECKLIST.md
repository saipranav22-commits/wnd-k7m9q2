# AERIS — Production Release & Submission Checklist

## 1. Product & Code Quality Verification

- [x] **Product Identity**: Original application named **AERIS — Wind Forecast Intelligence**, subtitle *Day-Ahead Wind Generation & Forecast Accuracy*.
- [x] **Data Scope Strictness**: Data restricted exclusively to Elexon BMRS `FUELHH` (wind actuals) and `WINDFOR` (forecasts). No extraneous third-party weather or energy sources added.
- [x] **Time Horizon**: Covers decision dates from 2026-01-01 through 2026-01-31, and delivery periods up to 2026-02-01.
- [x] **Offline Database Cache**: Verified local SQLite database containing 1,584 actuals and 19,272 forecasts on `E:\REintWindAnalytics\data\aeris.db`.
- [x] **Workspace Storage Compliance**: All code, `.venv`, npm cache, pip cache, and database strictly housed on Drive `E:\REintWindAnalytics`.
- [x] **Automated Tests**: 8 / 8 `pytest` automated tests passing (health, metadata, overview, decisions, accuracy, records, CSV export, point-in-time filtering).
- [x] **Frontend TypeScript Build**: `npm run build` passes with zero errors (`tsc && vite build`).
- [x] **Visual Design & Aesthetics**: Midnight navy theme (`#0B0F19`), teal/emerald primary accents, amber uncertainty bands, responsive layout, accessible typography.
- [x] **Browser Subagent E2E Verification**: Active browser test executed across all five operational views with recorded WebP session and captured screenshots.

---

## 2. Deliverables Checklist

### 2.1 Documentation Suite
- [x] `README.md`: Architecture, setup, local run, Docker, AI disclosure, and methodology.
- [x] `docs/ARCHITECTURE.md`: End-to-end architectural layer design and data flow.
- [x] `docs/DATA_METHODOLOGY.md`: Mathematical formulations, temporal alignment, and point-in-time rules.
- [x] `docs/REQUIREMENTS_MATRIX.md`: 25 traceability requirements mapped to code and validation status.
- [x] `docs/TEST_REPORT.md`: Test execution results, mathematical invariant proofs, and browser verification report.
- [x] `docs/DEMO_SCRIPT.md`: Precise 10-minute demonstration plan (Part 1: 5-min client pitch; Part 2: 5-min tech lead code review).
- [x] `docs/RELEASE_CHECKLIST.md`: This comprehensive verification checklist.

### 2.2 Docker & Local Deployment
- [x] `backend/Dockerfile`: Python 3.11/3.13 slim container with unified static serving.
- [x] `frontend/Dockerfile`: Multi-stage build with Nginx.
- [x] `docker-compose.yml`: Multi-container orchestration.
- [x] `.dockerignore` and `.env.example`.

### 2.3 Cloud Deployment Readiness (Vercel)
- [x] `vercel.json` configured for single or separated deployment.
- [x] Clean SPA routing and API proxy configuration.
- [x] CORS middleware configured to accept incoming web clients.

### 2.4 Video Demo (Submission Requirement)
- [x] Demonstration script created (`docs/DEMO_SCRIPT.md`).
- [x] Timing limits verified: maximum 5 minutes for Part 1, maximum 5 minutes for Part 2, maximum 10 minutes total.
- [ ] Record unlisted YouTube video following `docs/DEMO_SCRIPT.md`.
- [ ] Verify video URL in an incognito browser window.

### 2.5 Public Anonymous GitHub Repository (Submission Requirement)
- [x] Repository name anonymized (e.g. `aeris-wind-intelligence` or random token).
- [ ] Push clean commit history to GitHub.
- [ ] Verify repository visibility as Public in incognito mode.

### 2.6 Submission Form
- [ ] Open Microsoft Forms submission link: `https://forms.cloud.microsoft/r/Ljmf1aWESK`.
- [ ] Provide anonymous GitHub repository link.
- [ ] Provide unlisted YouTube video demo link.
- [ ] Provide deployed application link (Vercel/Heroku).
- [ ] Verify each URL in an incognito window before final submission.
