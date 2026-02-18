# Phase 1 — Data Foundation Design

**Date:** 2026-02-18
**PRD Reference:** `planning/prd.md` Sections 4.1–4.6, Phase 1

## Decision: Deterministic Generator with Hardcoded Exceptions

The ~10 exception-triggering records are hardcoded with exact values from the PRD's Exception Summary Matrix. The remaining ~40 normal records use seeded random generation for reproducibility.

## Files

```
capex-agent-demo/
├── data/
│   ├── generate_synthetic_data.py   # Single script, one function per CSV
│   ├── wbs_master.csv               # 50 rows
│   ├── itd_extract.csv              # 44 rows (3 missing, 3 zero-ITD)
│   ├── vow_estimates.csv            # 45 rows (2 missing VOW, 1 negative accrual)
│   ├── prior_period_accruals.csv    # 48 rows (1 large swing)
│   └── drill_schedule.csv           # ~60 rows (20 wells x 3-5 phases)
├── utils/
│   └── data_loader.py               # Plain functions, caching deferred to Phase 4
├── tests/
│   └── test_data.py                 # pytest, covers all 12 acceptance criteria
└── requirements.txt                 # pandas, openpyxl
```

## Exception Wiring (from PRD Section 4.6)

| Exception | WBS IDs | Mechanism |
|-----------|---------|-----------|
| Missing ITD (HIGH) | WBS-1031, WBS-1038, WBS-1044 | Absent from itd_extract.csv |
| Negative Accrual (HIGH) | WBS-1027 | ITD=$2,627K > VOW=$2,500K |
| Missing VOW (MEDIUM) | WBS-1015, WBS-1042 | Absent from vow_estimates.csv |
| Large Swing (MEDIUM) | WBS-1009 | Prior=$800K, Current=$1,072K (+34%) |
| Zero ITD (LOW) | WBS-1047, WBS-1048, WBS-1049 | itd_amount=0 in itd_extract.csv |

## Data Loader Design

- `load_csv(filename)` — reads CSV, returns DataFrame
- `load_wbs_master()`, `load_itd()`, `load_vow()`, `load_prior_accruals()`, `load_drill_schedule()` — typed wrappers
- No caching decorators yet (added in Phase 4 with `@st.cache_data`)

## Test Strategy

pytest assertions for all 12 Phase 1 acceptance criteria: row counts, column schemas, join gaps, exception triggers, dollar ranges, date sequencing, and row cap enforcement.
