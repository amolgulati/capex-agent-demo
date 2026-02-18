# **CapEx Driver-Based Forecasting Project Brief**

Architecture note: This document is deliberately generalized for external sharing. Names, timelines, costs, vendor technologies/configurations, governance specifics, and operational cadences have been removed or abstracted. Content represents options and concepts for discussion — not final; details are to be determined.

## **1. Project Overview**
The CapEx Forecasting initiative aims to build a **driver-based forecasting model** that replaces manual, spreadsheet-driven projections with a consistent, data-driven framework.
Unlike traditional time-series or statistical models, this approach anchors forecasts directly to **operational drivers**—such as well activity schedules and work-in-progress (WIP) estimates—providing finance teams with transparent, auditable, and automatically updating forecasts.

---

## **2. Objectives**
1. Automate the calculation of **monthly accruals** based on operational WIP inputs.  
2. Generate **forward-looking forecasts** tied to the latest **drill and frac schedules** for each business unit.  
3. Enable real-time updates as operations adjust schedules, eliminating the lag between physical activity and financial visibility.  
4. Provide **clear auditability and explainability** — every number traceable to ERP/source actuals, WIP inputs, or driver assumptions.  
5. Establish a scalable template that can be extended to Facilities and Maintenance categories.

---

## **3. Forecasting Framework**

### **3.1 Core Logic**
The model breaks down CapEx into three major components:

| Component | Definition | Source / Calculation |
|------------|-------------|----------------------|
| **ITD Costs** | Costs incurred to date on each project | Pulled directly from ERP/source systems |
| **Accrual** | Work performed but not yet booked | `Accrual = WIP – ITD` |
| **Outlook** | Future costs forecasted to complete the project | Derived from current **drill/frac schedule** and standard cost templates |

Each capital project (WBS) will therefore report:

---

### **3.2 Capital Forecasting Categories**
CapEx forecasts will be categorized by major project types:

1. **Drilling & Completions (D&C)** – well-level projects driven by the drill and frac schedule  
2. **Facility Projects** – infrastructure builds tied to milestone schedules  
3. **Maintenance Projects** – sustaining capital based on historical trends  
4. **Miscellaneous Projects** – ad hoc or low-materiality capital items  

Each **well-level WBS** will further break costs into four standardized categories:
- Drilling
- Completions
- Flowback
- Hookup  

---

### **3.3 Drill & Frac Schedule Integration**
Each Business Unit (BU) maintains its own **drill and frac schedules**, updated throughout the month.
These schedules form the **primary driver** for capital well forecasts.

For each well/project:
- The **drill schedule** provides start (spud) and end dates for drilling activity.
- The **frac schedule** provides completion and hookup timing.
- Costs are allocated to months using **Linear by Day allocation**:

#### **Outlook Allocation Formula (v1)**
```
Daily Rate = Total Phase Cost / Total Days in Phase
Monthly Allocation = Daily Rate × Days of Phase Activity in that Month
```

| Phase | Allocation Method |
|-------|-------------------|
| *Drilling* | Linear by Day: spud through drill end |
| *Completions* | Linear by Day: frac start through frac end |
| *Flowback* | Linear by Day: flowback start through flowback end |
| *Hookup* | Lump Sum: 100% allocated to hookup month |

**Edge Cases**:
- **In-progress phases**: Remaining Outlook = (Template Cost - ITD) allocated over remaining days
- **ITD ≥ Template Cost**: Outlook = $0, flagged for Finance review
- **Missing schedule dates**: Use average timing from similar wells (same basin/well type)

When the operational schedule changes, the model automatically recalculates the daily rate and realigns forecast timing.

---

### **3.4 Cost Estimation Logic**
- **Standard cost templates** define the baseline per-well cost for each category (e.g., drilling, completions).
- Costs can be adjusted for local factors (basin, depth, inflation, vendor pricing).
- **Accruals** are calculated monthly as the difference between the WIP estimate and ITD costs from source systems:
  ```
  Accrual = WIP - ITD
  ```
- **Outlook** is calculated using the Linear by Day method:
  ```
  Outlook = (Template Cost - ITD - Accrual) allocated across remaining phase days
  ```
- **Total Forecast** combines all components:
  ```
  Total Forecast = ITD + Accrual + Outlook
  ```

**v1 Simplifications**: The current implementation uses linear allocation only. Future versions may incorporate S-curve distributions, stage-count weighting for completions, and ML-based schedule prediction.

This provides a consistent, explainable forecast for every project and category.

---

## **4. Data Inputs and Ownership**

| Data Source | Description | Owner | Update Frequency |
|--------------|-------------|--------|------------------|
| **ERP/WBS Actuals** | Incurred-to-date (ITD) project costs | Accounting | Daily / Weekly |
| **Work-in-Progress (WIP) Estimates** | Operational estimate of work completed this period | Operations | Monthly |
| **Drill Schedule** | Planned and active wells with spud and drilling dates | BU Operations | Continuously updated |
| **Frac Schedule** | Completion, flowback, and hookup timing | BU Operations | Continuously updated |
| **Cost Estimate Templates** | Standard cost per phase (drilling, completions, flowback, hookup) | Finance / Engineering | Quarterly |
| **Project Master (AFE/WBS)** | Well/project metadata, basin, owner, in-service date | Finance / Master Data | Ongoing |

---

## **5. Key Outputs**

| Output | Description | Frequency | Primary Users |
|---------|--------------|------------|----------------|
| **Accrual File** | Monthly file to support accrual booking (`WIP – ITD`) | Monthly | Accounting |
| **Outlook Forecast File** | Monthly forecast by project, cost category, and month | Monthly | Finance / Planning |
| **Variance Report** | Actual vs WIP vs Outlook by project and BU | Monthly | Controllers / Management |
| **Spend Progress Report** | % Complete and S-curve visualizations | Monthly | Finance & Operations |

---

## **6. Governance and Cadence**

| Process | Owner | Cadence |
|----------|--------|----------|
| Drill & Frac Schedule Updates | BU Operations | Weekly / As Updated |
| WIP Submissions | Operations → Finance | Monthly |
| Data Refresh from ERP/Source Systems | IT / DevOps | Weekly or near real-time |
| Accrual Calculation | Accounting Innovation | Monthly |
| Forecast Generation & Review | BU Finance / Accounting Innovation | Monthly |
| Cost Template Updates | Finance / Engineering | Quarterly |

---

## **7. Design Principles**
1. **Driver-Driven:** Forecasts respond automatically to operational activity changes.  
2. **Transparent:** All calculations traceable to source data (ERP/source systems, WIP, or schedules).  
3. **Simple to Explain:** Accruals and forecasts easily reconcilable to ITD and project-level data.  
4. **Flexible:** Supports multiple project types (D&C, Facility, Maintenance, Misc.).  
5. **Extendable:** Designed to evolve toward hybrid driver + machine learning approaches once historical curves mature.

---

## **8. Next Steps**
1. Finalize **data contracts and owners** for ITD, WIP, drill schedule, and frac schedule feeds.
2. Define **standard cost templates** per well type and cost category.
3. Build **accrual calculation logic** (`WIP – ITD`).  
4. Develop **outlook generation logic** based on schedule timing and cost templates.  
5. Pilot with one BU’s drilling and completions data to validate methodology.  
6. Create standardized **output reports** and reconciliation views for accounting and planning.

---

## **9. Long-Term Vision**
Once established, this framework will serve as the foundation for:
- Integrated **Capital Lifecycle Reporting** (AFE to actuals)
- Predictive **Cost Curve Modeling** per basin and project type
- **Automated accrual generation** for monthly close
- Seamless integration into a centralized data platform and planning/analytics environment for unified financial forecasting

The end goal is a **single source of truth** for CapEx forecasts — dynamically tied to operational reality and ready for audit, analysis, and decision-making.
