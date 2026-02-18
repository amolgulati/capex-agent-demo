# **Technical Briefing: CapEx Driver-Based Forecasting**

Architecture note: This document is deliberately generalized for external sharing. Names, timelines, costs, vendor technologies/configurations, governance specifics, and operational cadences have been removed or abstracted. Content represents options and concepts for discussion — not final; details are to be determined.

## For Data Architect & Solutions Architect

**Purpose**: Provide technical overview and solicit expert feedback on architecture and design decisions
**Audience**: Data Architect, Solutions Architect, Planning Consultant

---

## **Table of Contents**

1. [Business Context](#1-business-context)
2. [Proposed Architecture](#2-proposed-architecture)
3. [Data Model Overview](#3-data-model-overview)
   - 3.3 [POC Data Minimum](#33-poc-data-minimum)
   - 3.4 [POC Exclusions](#34-poc-exclusions)
   - 3.5 [Data Quality Expectations](#35-data-quality-expectations)
   - 3.6 [POC Success Criteria](#36-poc-success-criteria)
4. [Calculation Logic](#4-calculation-logic)
5. [Key Technical Questions](#5-key-technical-questions)
   - 5.4 [Advanced Analytics Positioning](#54-advanced-analytics-positioning-datarobot--databricks)
6. [Next Steps](#6-next-steps)

---


## **1. Business Context**

### **1.1 The Problem**

Finance currently forecasts capital expenditures using manual Excel processes with significant pain points:
- 40-60 hours/month spent on manual accrual calculations
- 15-20% forecast variance
- 2-4 week lag between operational schedule changes and financial visibility
- Inconsistent methodologies across Business Units
- No traceability from operational schedules to financial forecasts

### **1.2 The Solution**

**Driver-based CapEx forecasting** integrated with operational schedules where:
- Forecasts auto-calculate from drill/frac schedules and cost templates
- Accruals calculated from work-in-progress (WIP) estimates
- Updates when operations adjusts schedules
- Single source of truth in centralized data platform
- Finance can audit every number back to source data

### **1.3 The Three-Component Forecasting Model**

Every capital project (WBS) forecast is broken into three components:

**Formula:** `Total Forecast = ITD + Accrual + Outlook`

| Component | Definition | Source |
|-----------|------------|--------|
| **ITD** | Invoice-to-Date (actuals) | ERP/source systems |
| **Accrual** | Work performed but not yet invoiced | WIP - ITD |
| **Outlook** | Future work forecasted | Schedule × Cost Templates |

**Example - Drilling Well #ABC123:**
- **ITD**: $2.3M (invoices posted to date)
- **Accrual**: $400K (rig finished drilling, invoice pending: WIP $2.7M - ITD $2.3M)
- **Outlook**: $3.8M (completion work scheduled for next 3 months)
- **Total Forecast**: $6.5M

### **1.4 Capital Project Categories**

**Phase 1 Focus:** Drilling & Completions (D&C) - well-level projects

Each well has 4 cost categories with different operational drivers:

| Cost Category | Operational Driver | Timing Logic |
|---------------|-------------------|--------------|
| **Drilling** | Drill schedule (spud date, duration) | Cost allocated from spud date through drill end |
| **Completions** | Frac schedule (frac stages, timing) | Cost allocated from frac start through completion |
| **Flowback** | Flowback schedule | Cost allocated during flowback period |
| **Hookup** | Hookup schedule (installation date) | Lump sum allocated to hookup month |

**Future Phases:** Facility Projects, Maintenance CapEx, Miscellaneous Projects

### **1.5 Success Criteria**

| Metric | Current State | Target |
|--------|---------------|--------|
| **Forecast Accuracy** | 15-20% variance | Single-digit variance on ITD + Accrual |
| **Time to Forecast** | 1-2 weeks | <1 day (automated) |
| **Driver Coverage** | 0% (all manual) | >90% of D&C tied to schedules |

---

## **2. Proposed Architecture**

### **2.1 High-Level Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                      SAP S/4HANA                                 │
│  • ACDOCA - ITD Actuals (WBS, GL, Amount)                       │
│  • WBS Master Data                                               │
└──────────────────┬──────────────────────────────────────────────┘
                   │ (Remote Table Connection)
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SAP DATASPHERE                                │
│                                                                  │
│  • Remote Tables: ITD Actuals, WBS Master Data                  │
│  • Operational Data: Drill Schedules, Frac Schedules, WIP       │
│  • Master Data: Cost Templates, BU Hierarchy                    │
│  • Results: Forecast Results, Audit Log                         │
│                                                                  │
└──────────┬────────────────────────────┬────────────────────────┘
           │                             │
           │ (Live Connection)           │ (Connection TBD)
           │                             ▼
           │              ┌─────────────────────────────────────┐
           │              │  CALCULATION ENGINE                  │
           │              │  **ARCHITECTURE DECISION NEEDED**   │
           │              │                                      │
           │              │  Options under consideration:        │
           │              │  • In-platform (Datasphere)          │
           │              │  • External compute (AWS/Databricks) │
           │              │                                      │
           │              │  Functions needed:                   │
           │              │  • Calculate Accruals (WIP - ITD)   │
           │              │  • Generate Outlook (Schedules)     │
           │              │  • Validate & Flag Exceptions       │
           │              └─────────────────────────────────────┘
           │                             │
           │                             │ (Write Results)
           │                             ▼
           │              [Forecast_Results Table in Datasphere]
           │
           ▼
┌─────────────────────────────────────────────────────────────────┐
│              SAC PLANNING MODEL: WIP Entry                       │
│  Purpose: Operations/Finance enters monthly work-done estimates │
│  Writeback: WIP Estimates table in Datasphere                   │
└──────────────────┬──────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                  SAC ANALYTICS (STORIES)                         │
│  • Accrual File Report (for month-end close)                    │
│  • Outlook Forecast Report (multi-year view)                    │
│  • Variance Analysis (Actual vs WIP vs Outlook)                 │
│  • Executive Dashboard (BU summary)                              │
└─────────────────────────────────────────────────────────────────┘
```

### **2.2 Key Architecture Questions**

**Calculation Engine Platform**:
- Should calculations run in-platform (Datasphere) or external?
- What are the trade-offs for each approach?

**Data Integration**:
- Is SAP Remote Tables the right approach for ACDOCA, or should we replicate?
- How should we handle operational schedule feeds (drill/frac data)?
- What's the preferred pattern for SAC Planning writeback to Datasphere?

---

## **3. Data Model Overview**

### **3.1 Data Tables**

**Source Data (Read-Only)**:
| Table | Source | Purpose |
|-------|--------|---------|
| ITD_Actuals | S/4HANA ACDOCA | Historical actuals for Accrual calculation |
| WBS_Master | S/4HANA PS module | Master data for cost templates and reporting |

**Operational Data (Updated by Operations)**:
| Table | Purpose | Key Attributes |
|-------|---------|----------------|
| Drill_Schedule | Timing driver for drilling outlook | WBS_ID, Spud_Date, Drill_End_Date, **Well_Type**, **Frac_Type** |
| Frac_Schedule | Timing driver for completion/flowback/hookup outlook | WBS_ID, Frac_Start/End, Hookup_Date, **Frac_Type** |
| WIP_Estimates | Work-done estimates for Accrual calculation (from SAC Planning) | WBS_ID, Period, Cost_Category, WIP_Amount |

*`Well_Type` and `Frac_Type` are descriptive dimensions (e.g., Horizontal/Vertical, Zipper/Plug-and-Perf). In v1, used for reporting segmentation; can optionally drive cost template selection when granular templates exist.*

**Master Data**:
| Table | Purpose |
|-------|---------|
| Cost_Templates | Unit costs by basin/well type for schedule-driven outlook |
| BU_Hierarchy | Reporting aggregation by cost center, BU, region |

**Results Data (Written by Calculation Engine)**:
| Table | Purpose |
|-------|---------|
| Forecast_Results | Final forecast output (ITD + Accrual + Outlook) |
| Calculation_Audit_Log | Audit trail and error tracking |

### **3.2 Key Relationships**

```
WBS_Master (1) ──→ (N) Drill_Schedule
WBS_Master (1) ──→ (N) Frac_Schedule
WBS_Master (1) ──→ (N) WIP_Estimates
WBS_Master (1) ──→ (N) ITD_Actuals
WBS_Master (N) ──→ (1) Cost_Templates (via Basin + Well Type)
WBS_Master (N) ──→ (1) BU_Hierarchy (via Cost Center)
```

---

### **3.3 POC Data Minimum**

To begin experimenting quickly, even with Excel-based inputs, the following minimum datasets are required:

#### **Required Excel Inputs (3 tabs minimum)**

| Tab | Purpose | Minimum Columns |
|-----|---------|-----------------|
| **Well_Master** | Well/project identifiers | `WBS_ID`, `Well_Name`, `Business_Unit`, `Basin`, `Well_Type`*, `AFE_Budget` |
| **Drill_Schedule** | Drilling timing | `WBS_ID`, `Spud_Date`, `Drill_End_Date`, `Well_Type`*, `Frac_Type`* |
| **Frac_Schedule** | Completion/hookup timing | `WBS_ID`, `Frac_Start_Date`, `Frac_End_Date`, `Hookup_Date`, `Frac_Type`* |
| **Cost_Templates** | Standard costs by phase | `Basin`, `Well_Type`, `Cost_Category`, `Standard_Cost` |
| **ITD_Actuals** *(or extract)* | Costs posted to date | `WBS_ID`, `Cost_Category`, `ITD_Amount` |

*\* `Well_Type` (e.g., Horizontal, Vertical) and `Frac_Type` (e.g., Zipper, Plug-and-Perf) are descriptive dimensions for v1. Used for reporting segmentation; optionally used to refine cost template selection when granular templates are available.*

#### **What Can Wait for Later Phases**
- Detailed GL/cost element breakdowns
- Vendor-level splits
- WIP estimates (can stub with ITD for initial testing)
- Stage counts and lateral lengths (nice-to-have for v2)

---

### **3.4 POC Exclusions**

The following are **explicitly out of scope** for the POC to prevent scope creep:

- GL/vendor-level forecasting
- Facilities and maintenance CapEx
- Automated approval workflows
- Schedule versioning and change tracking
- S-curves or non-linear allocation methods
- ML-generated forecast dollars (see [Advanced Analytics Positioning](#54-advanced-analytics-positioning))
- Cash flow timing or payment terms
- Multi-currency handling

---

### **3.5 Data Quality Expectations**

| Scenario | Handling | Audit Note |
|----------|----------|------------|
| **Missing schedule dates** | Flag as `ESTIMATED_SCHEDULE`; use median duration from similar wells (basin + well type) | Document imputation source |
| **Missing cost template** | Flag as `DEFAULT_TEMPLATE`; apply basin-level default with warning | Escalate for template creation |
| **ITD ≥ Template Cost** | Flag as `OVERRUN_REVIEW`; set Outlook = $0 | Requires Finance manual adjustment |
| **Invalid dates** (end < start) | Flag as `INVALID_SCHEDULE`; exclude from Outlook | Notify BU for correction |
| **Missing Well_Type/Frac_Type** | Flag as `MISSING_ATTRIBUTE`; use "Unknown" category | Track for data cleanup |

*Approach: Flag + fallback. The system generates a forecast using sensible defaults while clearly marking exceptions for review. All flags are audit-friendly and visible in output reports.*

---

### **3.6 POC Success Criteria**

The POC is successful if:

1. **Directional timing alignment** — Forecasted spend periods align within ±1 month of actual activity timing for 80%+ of wells
2. **Explainability** — Every forecast dollar traces to a schedule date and cost template (no black-box calculations)
3. **Reconciliation sanity** — `Total Forecast = ITD + Accrual + Outlook` holds for 100% of records
4. **Exception transparency** — All data quality issues are flagged, categorized, and visible in reports
5. **Stakeholder confidence** — Finance and Operations agree the methodology is reasonable for D&C wells

*Note: "Accuracy" (variance to actuals) is a future-state metric. POC focuses on methodology validation, not precision.*

---

## **4. Calculation Logic**

### **4.1 Accrual Calculation**

**Business Rule**: `Accrual = WIP - ITD`

For each WBS × Cost Category × Period:
1. Get WIP amount (work-done estimate from operations)
2. Get ITD amount (invoices posted to date from ACDOCA)
3. Calculate: Accrual = WIP - ITD
4. Validate:
   - Flag if Accrual is negative (invoices exceed work-done)
   - Flag if WIP > AFE Budget (overspend risk)

### **4.2 Outlook Calculation**

**Business Rule**: `Outlook = Scheduled Activity × Cost Template`

For each cost category:

**Drilling Outlook**:
- Look up standard drilling cost from Cost_Templates (by basin, well type)
- Allocate across months from spud date to drill end date
- If already drilling: prorate remaining cost

**Completions Outlook**:
- Look up standard completion cost from Cost_Templates
- Allocate across months from frac start to frac end

**Flowback Outlook**:
- Look up flowback cost from Cost_Templates
- Allocate to flowback period

**Hookup Outlook**:
- Look up hookup cost from Cost_Templates
- Allocate 100% to hookup month

### **4.2.1 Outlook Allocation Methodology (v1)**

This section defines the explicit methodology for allocating Outlook dollars across time periods.

#### **Core Method: Linear by Day**

All phase costs (except Hookup) are allocated using a **linear daily rate**:

```
Daily Rate = Total Phase Cost / Total Days in Phase
Monthly Allocation = Daily Rate × Days of Phase Activity in that Month
```

**Phase-Specific Rules**:

| Phase | Allocation Method | Formula |
|-------|-------------------|---------|
| **Drilling** | Linear by Day | Cost / (Drill End - Spud Date + 1) × days per month |
| **Completions** | Linear by Day | Cost / (Frac End - Frac Start + 1) × days per month |
| **Flowback** | Linear by Day | Cost / (Flowback End - Flowback Start + 1) × days per month |
| **Hookup** | Lump Sum | 100% allocated to hookup month |

#### **In-Progress Phase Handling**

When a phase has started but is not complete (calculation date falls within phase dates):

```
Remaining Outlook = (Total Phase Cost - ITD for that phase)
Allocation = Remaining Outlook / Remaining Days × days per month
```

- Use actual start date (from schedule) and scheduled end date
- Subtract ITD already incurred for that phase
- Allocate remaining cost over remaining calendar days

#### **Edge Case Handling**

| Scenario | Rule | System Behavior |
|----------|------|-----------------|
| **ITD ≥ Cost Template** | Do NOT auto-calculate Outlook | Set Outlook = $0, flag as `OVERRUN_REVIEW`, escalate to Finance |
| **Missing Schedule Dates** | Use average timing from similar wells | Query wells with same basin + well type, apply median phase duration, document in `Validation_Notes` |
| **Schedule Dates Shift** | Recalculate allocation | Rerun daily rate calculation with new dates, log variance vs prior run |
| **Phase End < Phase Start** | Invalid schedule | Flag as `INVALID_SCHEDULE`, exclude from Outlook, notify BU |

#### **Worked Example: Well WBS-2025-001**

**Well Attributes**:
- WBS: WBS-2025-001
- Basin: Permian
- Well Type: Horizontal

**Phase Schedule & Template Costs**:

| Phase | Start Date | End Date | Days | Template Cost |
|-------|------------|----------|------|---------------|
| Drilling | 2025-02-10 | 2025-03-15 | 33 | $2,400,000 |
| Completions | 2025-03-20 | 2025-04-10 | 21 | $3,200,000 |
| Flowback | 2025-04-11 | 2025-04-25 | 14 | $150,000 |
| Hookup | 2025-05-01 | 2025-05-01 | 1 | $250,000 |

**Monthly Outlook Allocation (as of Jan 31, 2025, before any work starts)**:

| Month | Drilling | Completions | Flowback | Hookup | Total |
|-------|----------|-------------|----------|--------|-------|
| Feb 2025 | $1,454,545 | $0 | $0 | $0 | $1,454,545 |
| Mar 2025 | $945,455 | $1,828,571 | $0 | $0 | $2,774,026 |
| Apr 2025 | $0 | $1,371,429 | $150,000 | $0 | $1,521,429 |
| May 2025 | $0 | $0 | $0 | $250,000 | $250,000 |
| **Total** | **$2,400,000** | **$3,200,000** | **$150,000** | **$250,000** | **$6,000,000** |

**Calculation Steps**:

1. **Drilling**: $2,400,000 / 33 days = $72,727/day
   - Feb 10-28 (19 days in Feb, but Feb 10-28 = 19 days): $72,727 × 20 = $1,454,545
   - Mar 1-15 (15 days, but phase has 13 remaining): $72,727 × 13 = $945,455

2. **Completions**: $3,200,000 / 21 days = $152,381/day
   - Mar 20-31 (12 days): $152,381 × 12 = $1,828,571
   - Apr 1-10 (10 days, but only 9 remaining in phase): $152,381 × 9 = $1,371,429

3. **Flowback**: $150,000 / 14 days = $10,714/day
   - Apr 11-25 (all 14 days in April): $150,000

4. **Hookup**: 100% in May = $250,000

#### **v1 Assumptions (Intentionally Simplified)**

The following simplifications apply to v1. These are documented for transparency and may evolve in future versions:

1. **Linear allocation only** - No S-curve or weighted distribution based on historical spend patterns
2. **Single cost template per well type/basin** - No depth or complexity adjustments
3. **Daily granularity** - Costs are calculated daily but reported monthly
4. **Deterministic** - No probabilistic modeling or confidence intervals
5. **Manual override for overruns** - No automatic cost re-estimation when ITD exceeds template
6. **Average-based imputation** - Missing schedules use simple averages, not ML prediction

#### **Future-State Enhancements (Planned)**

1. **S-curve allocation** - Allocate based on historical spend curves per phase
2. **Stage-count weighting** - For completions, weight by frac stages vs. calendar days
3. **ML-based schedule prediction** - Predict missing dates using well characteristics
4. **Automatic overrun forecasting** - Use historical patterns to estimate remaining cost on overruns
5. **Confidence intervals** - Provide probabilistic ranges on forecasts

### **4.3 Validation Rules**

| Rule | Description | Action |
|------|-------------|--------|
| Missing Schedule | WBS has no drill/frac schedule | Use average timing from similar wells (same basin/type); flag for review if no similar wells |
| Negative Accrual | ITD > WIP | Flag for operations review |
| Budget Overrun | WIP > AFE Budget | Flag for controller review |
| Missing Cost Template | No template for basin/well type | Use default with warning |
| **ITD ≥ Template Cost** | Actual costs meet or exceed planned cost before phase complete | Set Outlook = $0, flag as `OVERRUN_REVIEW`, escalate to Finance for manual adjustment |
| **Invalid Schedule Dates** | Phase end date before start date | Flag as `INVALID_SCHEDULE`, exclude from Outlook, notify BU operations |
| **Schedule Date Shift** | Dates changed from prior calculation | Recalculate allocation, log variance vs prior run in `Variance_vs_Prior_Run` |

---

## **5. Key Technical Questions**

### **5.1 For Data Architect**

1. **Platform Design**: Should we use calculation views heavily, or materialize results tables?

2. **Integration Pattern**: For ACDOCA, is Remote Table the best approach, or should we replicate for performance?

3. **Change Tracking**: How should we handle schedule changes (dates shift)? Do we need versioned data?

4. **Data Quality**: Recommended approach for data validation before calculations run?

5. **Security/RLS**: We need row-level security by BU. What's the preferred implementation pattern?

6. **Volume Considerations**: Any concerns with ~1,500 active wells, daily refresh, 24-month rolling outlook?

### **5.2 For Solutions Architect**

1. **Calculation Platform**: Where should calculations run? Trade-offs between in-platform vs external compute?

2. **Error Handling**: How should calculation failures be handled and communicated?

3. **Monitoring**: What observability/alerting should we build in?

4. **Testing Strategy**: How should we validate calculations before go-live?

### **5.3 For Planning Consultant**

1. **WIP Entry Form**: What's the best SAC Planning model design for monthly WIP submissions?

2. **Workflow**: Do we need approval workflows for WIP submissions?

3. **Reporting**: What SAC story designs work best for the output reports?

---

### **5.4 Advanced Analytics Positioning (DataRobot / Databricks)**

Tools like DataRobot and Databricks are positioned as **future enhancements** that augment—not replace—the driver-based approach. Potential use cases include: predicting phase durations based on well characteristics, flagging overrun risk before it materializes, imputing missing schedule data with higher accuracy than simple averages, and scaling feature engineering across large well populations.

**Early-phase constraint**: No ML-generated forecast dollars. The POC and initial production phases rely exclusively on transparent, auditable calculations (schedule × cost template). ML models may inform inputs (e.g., estimated drill days) but do not directly produce spend forecasts until the driver-based methodology is validated and stakeholder trust is established.

---

## **6. Next Steps**

**Immediate**:
- [ ] Architecture review session with Data Architect and Solutions Architect
- [ ] Planning model design session with SAC Consultant
- [ ] Agree on calculation platform approach

**Short-term**:
- [ ] Detailed data model design
- [ ] Integration pattern finalization
- [ ] Prototype development

**Your Input Needed**:
- Platform recommendations
- Data model design guidance
- Integration pattern best practices
- Risk identification
