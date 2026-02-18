# **CapEx Driver-Based Forecasting - Development Plan**
Architecture note: This document is deliberately generalized for external sharing. Names, timelines, costs, vendor technologies/configurations, governance specifics, and operational cadences have been removed or abstracted. Content represents options and concepts for discussion — not final; details are to be determined.

## **Document Overview**

This development plan provides a comprehensive roadmap for implementing the CapEx Driver-Based Forecasting system, focusing on the **Drilling & Completions (D&C) MVP**. The plan leverages a centralized data platform, a planning and analytics environment, and managed compute infrastructure to create a scalable, driver-based forecasting solution.

**Target Completion**: To be determined (TBD) for D&C MVP

---

## **Table of Contents**

1. [Executive Summary & Architecture](#1-executive-summary--architecture)
2. [Calculation Engine Options Analysis](#2-calculation-engine-options-analysis)
3. [Recommended Solution Architecture](#3-recommended-solution-architecture)
4. [Team Structure & Responsibilities](#4-team-structure--responsibilities)
5. [Implementation Phases](#5-implementation-phases)
6. [Technical Specifications](#6-technical-specifications)
7. [Data Models & Schema](#7-data-models--schema)
8. [Integration Patterns](#8-integration-patterns)
9. [Timeline & Milestones](#9-timeline--milestones)
10. [Risks & Mitigation Strategies](#10-risks--mitigation-strategies)
11. [Success Criteria & KPIs](#11-success-criteria--kpis)
12. [Future Roadmap](#12-future-roadmap)

---

## **1. Executive Summary & Architecture**

### **1.1 Solution Overview**

The CapEx Forecasting solution implements a **hybrid data platform + managed compute architecture** that:

- Stores curated master data and results in a **centralized data platform**
- Performs complex calculations in a **managed compute environment** (Python)
- Provides user interfaces and reporting through a **planning and analytics platform**
- Integrates with **ERP/source systems** for actual costs
- Leverages **object storage** for schedule data and file-based integrations

### **1.2 High-Level Architecture**

```
┌─────────────────┐
│  SAP S/4HANA    │
│   (ACDOCA)      │ ──────► ITD Actuals
└─────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│          SAP DATASPHERE                              │
│  ┌──────────────────────────────────────────┐       │
│  │  Data Models:                             │       │
│  │  - WBS Master                             │       │
│  │  - ITD Actuals (from S/4HANA)            │       │
│  │  - Drill & Frac Schedules                │       │
│  │  - WIP Estimates                         │       │
│  │  - Cost Templates                         │       │
│  │  - Forecast Results (Accrual + Outlook)  │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
         ▲                           │
         │                           ▼
    ┌─────────┐              ┌──────────────┐
    │  AWS    │              │   SAC        │
    │         │              │              │
    │ Lambda  │◄────────────►│ - Planning   │
    │ (Calc   │   Results    │ - Reporting  │
    │ Engine) │              │ - WIP Forms  │
    │         │              │ - Dashboards │
    └─────────┘              └──────────────┘
         ▲
         │
    ┌─────────┐
    │  AWS S3 │
    │ Drill/  │
    │ Frac    │
    │ Files   │
    └─────────┘
```

### **1.3 Key Design Decisions**

| Decision Area | Choice | Rationale |
|---------------|--------|-----------|
| **Data Storage** | Centralized Data Platform | Single source of truth, integration with ERP and analytics |
| **Calculation Engine** | Managed Compute (Python) | Flexibility for complex logic, team Python expertise, aligns with analytics projects |
| **User Interface** | Planning & Analytics Platform | Finance team familiarity, planning capabilities, integration with data platform |
| **Schedule Integration** | Object Storage → Data Platform | Supports multiple BU formats, flexible ingestion patterns |
| **WIP Data Entry** | Planning Forms | User-friendly, integrated workflow, audit trail |
| **Execution Frequency** | Batch execution | Balances timeliness with system performance |

---

## **2. Calculation Engine Options Analysis**

### **2.1 Option A: Planning Platform**

**Architecture**: All calculations performed within SAC Planning using Data Actions and Advanced Formulas

#### **Pros**
- ✅ **Native SAP Integration**: Seamless with Datasphere and SAC reporting
- ✅ **Single Platform**: No external systems to manage
- ✅ **Finance Team Ownership**: Finance Reporting team can maintain
- ✅ **Built-in Planning Features**: Versions, allocations, approval workflows
- ✅ **Real-time Calculations**: Instant user feedback on data entry
- ✅ **Lower Infrastructure Cost**: No additional AWS compute costs

#### **Cons**
- ❌ **Limited Complexity**: Advanced formulas have performance limitations
- ❌ **Scale Constraints**: Large data volumes (1000+ wells) may cause performance issues
- ❌ **Debugging Difficulty**: Limited troubleshooting tools vs traditional code
- ❌ **Version Control**: Data Actions not as easily version-controlled as code
- ❌ **External Data**: Harder to integrate Python libraries or ML models
- ❌ **Testing**: No unit testing framework, harder to validate logic

**Best For**: Simpler calculation logic, smaller data volumes (<500 wells), finance team-led projects

---

### **2.2 Option B: Managed Compute + Python**

**Architecture**: Calculations performed in AWS Lambda functions, results written to Datasphere

#### **Pros**
- ✅ **Computational Power**: Handle complex logic, large datasets efficiently
- ✅ **Flexibility**: Use pandas, numpy, custom algorithms
- ✅ **Version Control**: Full Git-based code management
- ✅ **Testing**: Comprehensive unit testing, CI/CD pipelines
- ✅ **Extensibility**: Easy to add ML models, advanced analytics
- ✅ **Team Expertise**: Data Science team skilled in Python
- ✅ **Reusability**: Logic can be shared across projects
- ✅ **Debugging**: Standard Python debugging tools

#### **Cons**
- ❌ **Multi-System Complexity**: Additional integration points
- ❌ **Operational Overhead**: More infrastructure to monitor and maintain
- ❌ **Development Time**: Longer initial setup vs SAC native
- ❌ **Team Dependencies**: Requires Data Science team involvement
- ❌ **Cost**: AWS Lambda execution costs (though minimal for daily batch)
- ❌ **Latency**: Slight delay vs real-time SAC calculations

**Best For**: Complex logic, large scale, ML integration, data science team collaboration

---

### **2.3 Recommended Approach: Hybrid with Managed Compute Primary**

**Recommendation**: Use **AWS Lambda for core calculation engine** with SAC for presentation and simple user interactions

#### **Rationale**

1. **Complexity**: The forecasting logic (schedule-based cost allocation, multi-phase timing) is moderately complex
2. **Scale**: Expected to grow to 1000+ wells across multiple BUs
3. **Future-Proofing**: Document mentions "hybrid driver + machine learning approaches" - AWS enables this
4. **Existing Infrastructure**: Already using AWS SageMaker for ML projects
5. **Team Capabilities**: Data Science team can own calculation engine, Finance Reporting owns SAC layer

#### **Hybrid Architecture Benefits**

- **AWS Lambda**: Handles accrual calculations, outlook generation, cost allocation
- **Planning Platform**: Manages WIP data entry, user overrides, manual adjustments
- **SAC Analytics**: Provides reporting, dashboards, variance analysis
- **Datasphere**: Central data repository connecting both systems

---

## **3. Recommended Solution Architecture**

### **3.1 Component Diagram**

```
┌──────────────────────────────────────────────────────────────┐
│                         AWS ENVIRONMENT                       │
│                                                               │
│  ┌─────────────┐      ┌──────────────────┐                  │
│  │   S3 Bucket │      │  Lambda Function │                  │
│  │             │      │                  │                  │
│  │ - Drill     │─────►│  capex_forecast_ │                  │
│  │   Schedule  │      │  calculator      │                  │
│  │ - Frac      │      │                  │                  │
│  │   Schedule  │      │  Components:     │                  │
│  │ - Cost      │      │  - Accrual calc  │                  │
│  │   Templates │      │  - Outlook calc  │                  │
│  └─────────────┘      │  - Cost alloc    │                  │
│         │             │  - Schedule proc │                  │
│         │             └──────────────────┘                  │
│         │                      │                             │
│  ┌──────▼──────┐              │                             │
│  │ EventBridge │              │                             │
│  │ (Daily 6AM) │──────────────┘                             │
│  └─────────────┘                                            │
│         │                                                    │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼ (Trigger)
┌──────────────────────────────────────────────────────────────┐
│              SAP DATASPHERE                                   │
│                                                               │
│  ┌─────────────────┐     ┌──────────────────┐               │
│  │  Source Tables  │     │  Calculation     │               │
│  │  (Live/Remote)  │     │  Views           │               │
│  │                 │     │                  │               │
│  │ - SAP_ITD_      │     │ - CV_WBS_        │               │
│  │   Actuals       │────►│   Summary        │               │
│  │ - WIP_Estimates │     │ - CV_Forecast_   │               │
│  │ - Drill_        │     │   Monthly        │               │
│  │   Schedule      │     │ - CV_Variance_   │               │
│  │ - Frac_Schedule │     │   Analysis       │               │
│  │ - Cost_         │     └──────────────────┘               │
│  │   Templates     │              │                          │
│  │                 │              │                          │
│  │ ┌─────────────┐ │              │                          │
│  │ │ Forecast_   │ │◄─────────────┘                          │
│  │ │ Results     │ │ (from Lambda)                          │
│  │ │ (Writeback) │ │                                         │
│  │ └─────────────┘ │                                         │
│  └─────────────────┘                                         │
│         │                                                    │
└─────────┼────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────┐
│              SAP ANALYTICS CLOUD                              │
│                                                               │
│  ┌──────────────────┐    ┌──────────────────┐               │
│  │  Planning Model  │    │  Stories         │               │
│  │                  │    │  (Reports)       │               │
│  │ - WIP Data Entry │    │                  │               │
│  │ - Manual Adj.    │    │ - Accrual File   │               │
│  │ - Cost Override  │    │ - Outlook Rpt    │               │
│  └──────────────────┘    │ - Variance Rpt   │               │
│                          │ - S-Curve Viz    │               │
│                          │ - BU Dashboard   │               │
│                          └──────────────────┘               │
└──────────────────────────────────────────────────────────────┘
```

### **3.2 Technology Stack**

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Data Warehouse** | SAP Datasphere | Master data, actuals, forecast results |
| **ERP Source** | SAP S/4HANA | ACDOCA actuals (ITD costs) |
| **Calculation Engine** | AWS Lambda (Python 3.11) | Accrual & outlook calculations |
| **Data Storage** | AWS S3 | Schedule files, cost templates |
| **Orchestration** | AWS EventBridge | Daily job scheduling |
| **Data Integration** | AWS Glue (optional) | Schedule file parsing & validation |
| **Planning & Forms** | Planning Platform | WIP entry, manual adjustments |
| **Reporting** | SAC Stories | Dashboards, variance reports |
| **Version Control** | Git (GitHub/GitLab) | Lambda code, SQL scripts |
| **CI/CD** | GitHub Actions / AWS CodePipeline | Automated testing & deployment |

### **3.3 Key AWS Components**

#### **Lambda Function: `capex_forecast_calculator`**

**Runtime**: Python 3.11
**Memory**: 2048 MB
**Timeout**: 5 minutes
**Trigger**: EventBridge (daily 6:00 AM)

**Dependencies**:
- `pandas` - Data manipulation
- `numpy` - Numerical calculations
- `boto3` - S3 access
- `pyodbc` / `sqlalchemy` - Datasphere connection
- `python-dateutil` - Date calculations

**Environment Variables**:
- `DATASPHERE_CONNECTION_STRING`
- `S3_BUCKET_NAME`
- `CALCULATION_DATE` (override for testing)

---

## **4. Team Structure & Responsibilities**

### **4.1 Team Roles Matrix**

| Team | Primary Responsibilities | Deliverables |
|------|-------------------------|--------------|
| **Finance SMEs** | - Business requirements<br>- Calculation logic validation<br>- Cost template definition<br>- UAT testing<br>- Change management | - Requirements doc<br>- Test scenarios<br>- Sign-off on calculations |
| **Finance Reporting Team** | - Data platform modeling<br>- Analytics story development<br>- Planning model setup<br>- View creation<br>- User training | - Data platform schema<br>- Reports<br>- WIP entry forms<br>- User guides |
| **IT Data Science Team** | - Lambda function development<br>- Calculation algorithm coding<br>- Unit testing<br>- Performance optimization<br>- Code documentation | - Python calculation engine<br>- Unit tests<br>- API documentation |
| **Centralized AI Team** | - Architecture review<br>- ML integration planning<br>- Code quality standards<br>- Future ML model development | - Architecture approval<br>- ML roadmap<br>- Best practices guide |
| **IT SAP Team** | - S/4HANA connection setup<br>- Datasphere infrastructure<br>- SAC tenant management<br>- Security & authorization<br>- Production support | - Live connections<br>- Security setup<br>- Monitoring dashboards |

### **4.2 RACI Matrix - Key Deliverables**

| Deliverable | Finance SMEs | Fin Reporting | Data Science | AI Team | SAP Team |
|-------------|--------------|---------------|--------------|---------|----------|
| Requirements | **R** | C | C | I | I |
| Datasphere Schema | C | **R** | C | I | A |
| Lambda Calculations | **A** | C | **R** | C | I |
| SAC Reports | C | **R** | I | I | C |
| S/4HANA Connection | I | C | I | I | **R** |
| UAT Testing | **R** | C | C | I | C |
| Production Deployment | A | C | C | I | **R** |

**Legend**: R = Responsible, A = Accountable, C = Consulted, I = Informed

---

## **5. Implementation Phases**

### **Phase 1: Foundation & Datasphere Data Models** (Weeks 1-3)

#### **Objectives**
- Establish Datasphere data foundation
- Connect to SAP S/4HANA for ITD actuals
- Define data model schema for all entities

#### **Key Activities**

**Week 1: Planning & Setup**
- [ ] Kickoff meeting with all teams
- [ ] Finalize requirements with Finance SMEs
- [ ] Set up development Datasphere space
- [ ] Create Git repository for code assets
- [ ] Define naming conventions and standards

**Week 2: S/4HANA Integration**
- [ ] Configure live connection to S/4HANA
- [ ] Create remote table for ACDOCA (ITD actuals)
- [ ] Map WBS elements and cost elements
- [ ] Create initial data validation queries
- [ ] Test data refresh latency

**Week 3: Datasphere Data Model**
- [ ] Create WBS Master table
- [ ] Create Drill Schedule table
- [ ] Create Frac Schedule table
- [ ] Create WIP Estimates table
- [ ] Create Cost Templates table
- [ ] Create Forecast Results table (accrual + outlook)
- [ ] Define relationships and primary keys
- [ ] Create initial calculation views

#### **Deliverables**
- ✅ Datasphere space configured
- ✅ Live S/4HANA connection active
- ✅ All base tables created
- ✅ Data dictionary documented
- ✅ Initial data loaded for pilot BU

#### **Team Assignments**
- **Lead**: Finance Reporting Team
- **Support**: IT SAP Team, Finance SMEs

---

### **Phase 2: Data Ingestion & Integration** (Weeks 3-5)

#### **Objectives**
- Establish schedule data ingestion from S3
- Create WIP data entry capability
- Build cost template management

#### **Key Activities**

**Week 3-4: Schedule Data Pipeline**
- [ ] Define drill schedule file format (CSV/Excel)
- [ ] Define frac schedule file format
- [ ] Create S3 bucket structure (`/drill-schedules/`, `/frac-schedules/`)
- [ ] Build Datasphere flow to read from S3
- [ ] Implement data validation rules
- [ ] Create error handling and logging
- [ ] Test with pilot BU schedule files

**Week 4-5: WIP & Templates**
- [ ] Design planning model for WIP entry
- [ ] Create WIP input form (by WBS, month)
- [ ] Build cost template upload capability
- [ ] Implement template versioning
- [ ] Create data quality checks
- [ ] Set up user security roles

#### **Deliverables**
- ✅ S3 → Datasphere integration working
- ✅ Schedule data flowing daily
- ✅ WIP input form operational
- ✅ Cost templates loaded and versioned

#### **Team Assignments**
- **Lead**: Finance Reporting Team (SAC), IT Data Science Team (S3 integration)
- **Support**: IT SAP Team, Finance SMEs

---

### **Phase 3: Calculation Engine Development** (Weeks 5-9)

#### **Objectives**
- Build AWS Lambda calculation engine
- Implement accrual calculation logic
- Develop outlook forecasting algorithm
- Integrate with Datasphere

#### **Key Activities**

**Week 5-6: Lambda Setup & Accrual Logic**
- [ ] Set up AWS Lambda function
- [ ] Configure Datasphere connection (ODBC/JDBC)
- [ ] Implement data extraction from Datasphere
- [ ] Build accrual calculation: `WIP - ITD`
- [ ] Handle edge cases (negative accruals, missing data)
- [ ] Write unit tests for accrual logic
- [ ] Test with sample data

**Week 6-7: Outlook Forecasting Engine**
- [ ] Implement schedule parsing logic
- [ ] Build cost allocation algorithm by phase:
  - Drilling: spud to drill end
  - Completions: frac start to frac end
  - Hookup: hookup month
  - Electricity: post-hookup
- [ ] Apply cost templates to schedule
- [ ] Calculate monthly cost distribution
- [ ] Implement adjustments (basin, depth factors)
- [ ] Write unit tests for outlook logic

**Week 7-8: Integration & Optimization**
- [ ] Build Datasphere writeback logic
- [ ] Implement incremental vs full refresh
- [ ] Add error handling and retry logic
- [ ] Optimize for performance (vectorization)
- [ ] Create CloudWatch logging and monitoring
- [ ] Set up EventBridge daily trigger (6:00 AM)
- [ ] End-to-end integration testing

**Week 8-9: Testing & Validation**
- [ ] Test with full pilot BU dataset
- [ ] Validate calculations vs manual spreadsheets
- [ ] Performance testing (1000+ wells)
- [ ] Reconciliation with Finance SMEs
- [ ] Fix any calculation discrepancies
- [ ] Documentation of calculation logic

#### **Deliverables**
- ✅ Lambda function deployed and running daily
- ✅ Accrual calculations validated
- ✅ Outlook forecasts generated
- ✅ Results written to Datasphere
- ✅ Calculation documentation complete

#### **Team Assignments**
- **Lead**: IT Data Science Team
- **Support**: Finance SMEs (validation), Centralized AI Team (code review)

---

### **Phase 4: SAC Reporting & User Interface** (Weeks 8-11)

#### **Objectives**
- Build SAC stories for all key outputs
- Create interactive dashboards
- Implement variance analysis

#### **Key Activities**

**Week 8-9: Core Reports**
- [ ] Create Accrual File report
  - By WBS, BU, month
  - Drill-down to well level
  - Export to Excel
- [ ] Create Outlook Forecast File report
  - Monthly forecast by cost category
  - Multi-year view
  - Scenario comparison
- [ ] Create Variance Report
    - Actual vs WIP vs Outlook
  - Waterfall charts
  - Trend analysis

**Week 9-10: Dashboards & Visualizations**
- [ ] Build Executive Dashboard
  - BU-level summary cards
  - YTD vs forecast
  - Key metrics (accrual %, variance)
- [ ] Create S-Curve Progress Report
  - Project % complete
  - Spend curves by project
  - Milestone tracking
- [ ] Build Well-Level Detail View
  - Schedule timeline
  - Cost breakdown by phase
  - ITD vs forecast comparison

**Week 10-11: Interactivity & Filtering**
- [ ] Add dynamic filters (BU, basin, month, project type)
- [ ] Implement drill-down navigation
- [ ] Create bookmark views for common analyses
- [ ] Add input controls for scenario planning
- [ ] Build export templates
- [ ] Mobile optimization

#### **Deliverables**
- ✅ All 4 core reports operational
- ✅ Executive dashboard deployed
- ✅ S-curve visualizations working
- ✅ User navigation intuitive

#### **Team Assignments**
- **Lead**: Finance Reporting Team
- **Support**: Finance SMEs (requirements), IT SAP Team (permissions)

---

### **Phase 5: Pilot Testing & Validation** (Weeks 10-13)

#### **Objectives**
- Pilot with single BU's D&C portfolio
- Validate end-to-end workflow
- Reconcile with existing processes
- Gather user feedback

#### **Key Activities**

**Week 10-11: Pilot BU Setup**
- [ ] Select pilot BU (largest or most complex)
- [ ] Load historical data (6 months)
- [ ] Configure cost templates for pilot BU
- [ ] Upload current drill and frac schedules
- [ ] Train pilot users on WIP entry
- [ ] Run initial forecast calculations

**Week 11-12: Validation & Reconciliation**
- [ ] Compare system accruals to manual calculations
- [ ] Reconcile outlook to existing forecasts
- [ ] Validate ITD actuals against SAP reports
- [ ] Test schedule change scenarios
- [ ] Verify monthly close process integration
- [ ] Document any calculation variances

**Week 12-13: User Acceptance Testing**
- [ ] Finance SMEs test WIP entry workflow
- [ ] Controllers review variance reports
- [ ] Operations validate schedule integration
- [ ] Test report exports and deliverables
- [ ] Collect user feedback
- [ ] Prioritize and implement fixes
- [ ] Create user training materials

#### **Deliverables**
- ✅ Pilot BU fully operational
- ✅ Calculations reconciled and validated
- ✅ User acceptance sign-off
- ✅ Training materials created
- ✅ Issue log and remediation plan

#### **Team Assignments**
- **Lead**: Finance SMEs (validation), Finance Reporting Team (support)
- **Support**: All teams for bug fixes

---

### **Phase 6: Production Deployment & Rollout** (Weeks 13-16)

#### **Objectives**
- Deploy to production environment
- Onboard remaining BUs
- Establish support processes
- Transition to operations

#### **Key Activities**

**Week 13-14: Production Deployment**
- [ ] Migrate Lambda to production AWS account
- [ ] Configure production Datasphere space
- [ ] Set up production SAC tenant stories
- [ ] Implement backup and disaster recovery
- [ ] Configure monitoring and alerting
- [ ] Create production support runbook
- [ ] Conduct security review

**Week 14-15: Remaining BU Rollout**
- [ ] Schedule training sessions per BU
- [ ] Load historical data for all BUs
- [ ] Configure BU-specific cost templates
- [ ] Upload current schedules for all BUs
- [ ] Conduct dry-run of monthly close
- [ ] Validate cross-BU reporting

**Week 15-16: Transition to Operations**
- [ ] Knowledge transfer to support teams
- [ ] Document troubleshooting procedures
- [ ] Establish monthly calendar and cadence
- [ ] Set up governance committee
- [ ] Create change request process
- [ ] Schedule first monthly close
- [ ] Post-implementation review

#### **Deliverables**
- ✅ Production system live for all D&C BUs
- ✅ All users trained
- ✅ Support processes established
- ✅ Monthly close calendar set
- ✅ Lessons learned documented

#### **Team Assignments**
- **Lead**: IT SAP Team (deployment), Finance Reporting Team (training)
- **Support**: All teams

---

## **6. Technical Specifications**

### **6.1 AWS Lambda Function Specification**

#### **Function: `capex_forecast_calculator`**

**Entry Point**: `lambda_handler.py`

```python
# Pseudo-code structure
def lambda_handler(event, context):
    """
    Main entry point for CapEx forecast calculation
    Triggered daily by EventBridge
    """
    try:
        # 1. Initialize connections
        datasphere_conn = get_datasphere_connection()
        s3_client = boto3.client('s3')

        # 2. Extract data from Datasphere
        itd_actuals = extract_itd_actuals(datasphere_conn)
        wip_estimates = extract_wip_estimates(datasphere_conn)
        drill_schedule = extract_drill_schedule(datasphere_conn)
        frac_schedule = extract_frac_schedule(datasphere_conn)
        cost_templates = extract_cost_templates(datasphere_conn)

        # 3. Calculate Accruals
        accruals = calculate_accruals(wip_estimates, itd_actuals)

        # 4. Generate Outlook Forecast
        outlook = generate_outlook(
            drill_schedule,
            frac_schedule,
            cost_templates,
            itd_actuals,
            accruals
        )

        # 5. Write results back to Datasphere
        write_accruals(datasphere_conn, accruals)
        write_outlook(datasphere_conn, outlook)

        # 6. Log summary
        log_calculation_summary(accruals, outlook)

        return {
            'statusCode': 200,
            'body': json.dumps('Forecast calculation completed successfully')
        }

    except Exception as e:
        log_error(e)
        send_alert_to_team(e)
        raise
```

#### **Core Modules**

**Module: `accrual_calculator.py`**
```python
def calculate_accruals(wip_df, itd_df):
    """
    Calculate accruals as WIP - ITD

    Input:
        wip_df: DataFrame with columns [WBS, Month, WIP_Amount]
        itd_df: DataFrame with columns [WBS, ITD_Amount]

    Output:
        DataFrame with columns [WBS, Month, Accrual_Amount]
    """
    # Merge WIP and ITD on WBS
    # Calculate accrual = WIP - ITD
    # Handle negative accruals (flag for review)
    # Return accrual dataset
```

**Module: `outlook_generator.py`**
```python
def generate_outlook(drill_sched, frac_sched, cost_templates, itd, accruals):
    """
    Generate forward-looking forecast based on schedules

    Steps:
    1. For each well in drill/frac schedule:
       a. Determine phase timings (drill, completion, hookup, elec)
       b. Apply cost template rates
       c. Allocate costs to months based on phase duration
    2. Calculate total estimated cost per well
    3. Subtract ITD and accrual to get outlook
    4. Return monthly forecast by WBS and cost category
    """

def allocate_costs_to_months(phase_start: date, phase_end: date, total_cost: float,
                             itd_amount: float = 0.0) -> dict:
    """
    Allocate phase costs to months using Linear by Day method.

    Formula:
        Daily Rate = (Total Cost - ITD) / Total Days in Phase
        Monthly Allocation = Daily Rate × Days of Phase Activity in that Month

    Args:
        phase_start: Phase start date (e.g., spud date for drilling)
        phase_end: Phase end date (e.g., drill end date)
        total_cost: Total phase cost from Cost_Templates
        itd_amount: Incurred-to-date costs already posted (default 0 for future phases)

    Returns:
        dict: {YYYY-MM: allocated_amount} for each month in phase

    Example:
        >>> allocate_costs_to_months(date(2025, 2, 10), date(2025, 3, 15), 2400000, 0)
        {'2025-02': 1454545.45, '2025-03': 945454.55}

    Edge Cases:
        - If itd_amount >= total_cost: Return empty dict, flag as OVERRUN_REVIEW
        - If phase_end < phase_start: Return empty dict, flag as INVALID_SCHEDULE
    """
    remaining_cost = total_cost - itd_amount
    if remaining_cost <= 0:
        return {}  # Overrun - handled by calling function

    total_days = (phase_end - phase_start).days + 1
    daily_rate = remaining_cost / total_days

    monthly_allocation = {}
    current_date = phase_start
    while current_date <= phase_end:
        month_key = current_date.strftime('%Y-%m')
        # Count days in this month within phase
        month_end = min(phase_end, last_day_of_month(current_date))
        days_in_month = (month_end - current_date).days + 1
        monthly_allocation[month_key] = daily_rate * days_in_month
        current_date = first_day_of_next_month(current_date)

    return monthly_allocation


def handle_overrun(wbs_id: str, phase: str, itd_amount: float,
                   template_cost: float) -> dict:
    """
    Handle case where ITD meets or exceeds template cost (overrun scenario).

    Business Rule: Do NOT auto-calculate Outlook when ITD >= Template Cost.
    Set Outlook = $0 and flag for manual Finance review.

    Args:
        wbs_id: Work Breakdown Structure identifier
        phase: Cost category (Drilling, Completions, Flowback, Hookup)
        itd_amount: Actual costs incurred to date
        template_cost: Expected cost from Cost_Templates

    Returns:
        dict: Validation result with status and notes

    Example:
        >>> handle_overrun('WBS-2025-001', 'Drilling', 2500000, 2400000)
        {
            'outlook_amount': 0,
            'validation_status': 'OVERRUN_REVIEW',
            'validation_notes': 'ITD ($2,500,000) exceeds template ($2,400,000). Manual review required.'
        }
    """
    return {
        'outlook_amount': 0,
        'validation_status': 'OVERRUN_REVIEW',
        'validation_notes': f'ITD (${itd_amount:,.0f}) exceeds template (${template_cost:,.0f}). Manual review required.'
    }


def estimate_missing_schedule(wbs_id: str, basin: str, well_type: str,
                              phase: str, conn) -> dict:
    """
    Estimate missing schedule dates using averages from similar wells.

    Business Rule: When schedule dates are missing, use median phase duration
    from wells with same basin and well_type.

    Args:
        wbs_id: Work Breakdown Structure identifier
        basin: Geographic basin (e.g., 'Permian', 'Eagle Ford')
        well_type: Well classification (e.g., 'Horizontal', 'Vertical')
        phase: Cost category to estimate (Drilling, Completions, Flowback, Hookup)
        conn: Database connection for querying similar wells

    Returns:
        dict: Estimated dates and validation notes

    Example:
        >>> estimate_missing_schedule('WBS-2025-001', 'Permian', 'Horizontal', 'Drilling', conn)
        {
            'estimated_start': date(2025, 3, 1),
            'estimated_end': date(2025, 4, 3),
            'estimated_days': 33,
            'validation_status': 'ESTIMATED_SCHEDULE',
            'validation_notes': 'Drilling dates estimated from 47 similar Permian Horizontal wells (median 33 days)'
        }
    """
    # Query median phase duration from similar wells
    query = '''
        SELECT MEDIAN(DATEDIFF(day, phase_start, phase_end)) as median_days,
               COUNT(*) as well_count
        FROM schedule_history
        WHERE basin = ? AND well_type = ? AND phase = ?
    '''
    result = conn.execute(query, (basin, well_type, phase))
    median_days, well_count = result.fetchone()

    if well_count == 0:
        return {
            'validation_status': 'MISSING_SCHEDULE',
            'validation_notes': f'No similar wells found for {basin} {well_type}. Manual entry required.'
        }

    # Estimate start date as today + buffer, end as start + median_days
    estimated_start = date.today() + timedelta(days=30)  # Assume 30-day buffer
    estimated_end = estimated_start + timedelta(days=median_days)

    return {
        'estimated_start': estimated_start,
        'estimated_end': estimated_end,
        'estimated_days': median_days,
        'validation_status': 'ESTIMATED_SCHEDULE',
        'validation_notes': f'{phase} dates estimated from {well_count} similar {basin} {well_type} wells (median {median_days} days)'
    }


def apply_adjustment_factors(base_cost, basin, depth):
    """
    Apply basin and depth adjustment factors to base cost.

    Note: v1 uses single cost template per well type/basin without
    depth adjustments. This function is a placeholder for future enhancements.
    """
```

**Module: `datasphere_connector.py`**
```python
def get_datasphere_connection():
    """
    Establish connection to Datasphere using ODBC/JDBC
    """

def extract_itd_actuals(conn):
    """
    Query: SELECT WBS, SUM(Amount) as ITD FROM SAP_ITD_Actuals GROUP BY WBS
    """

def write_accruals(conn, accruals_df):
    """
    Truncate and reload Forecast_Results table (accrual records)
    """
```

---

### **6.2 Performance Requirements**

| Metric | Target | Notes |
|--------|--------|-------|
| **Lambda Execution Time** | < 3 minutes | For 1000 wells |
| **Datasphere Query Time** | < 30 seconds | Per extract query |
| **SAC Report Load Time** | < 5 seconds | Executive dashboard |
| **Data Freshness** | Daily by 8 AM | After 6 AM Lambda run |
| **Concurrent Users** | 50+ | SAC planning forms |
| **Data Volume** | 5000+ wells | Future state |

---

### **6.3 Lambda Layers & Shared Libraries**

#### **Modular Code Structure**

To improve maintainability and support multiple developers, organize Lambda code into reusable modules using **AWS Lambda Layers**:

**Lambda Layer: `capex-common-lib`**

Contains shared libraries used across all calculation functions:

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `schedule_parser.py` | Parse BU-specific schedule file formats | `parse_drill_schedule()`, `parse_frac_schedule()`, `validate_schedule_format()` |
| `cost_allocator.py` | Cost allocation logic across phases | `allocate_drilling_costs()`, `allocate_completion_costs()`, `allocate_by_month()` |
| `datasphere_io.py` | Datasphere connection and I/O | `get_connection()`, `read_table()`, `write_table()`, `bulk_insert()` |
| `validation.py` | Data quality checks | `validate_accrual()`, `check_reconciliation()`, `flag_anomalies()` |
| `config.py` | Configuration management | Load environment variables, constants |

**Benefits**:
- Code reuse across multiple Lambda functions
- Easier unit testing of individual modules
- Version control for shared logic
- Faster deployment (layers cached separately)
- Multiple developers can work on different modules

#### **Layer Versioning**

- Each layer tagged with semantic version (e.g., `v1.2.0`)
- Lambda functions reference specific layer version
- Allows rollback if new version has issues
- Production uses latest stable version

#### **Deployment Structure**

```
capex-forecasting/
├── lambda/
│   ├── forecast_calculator/
│   │   ├── lambda_handler.py        # Main entry point
│   │   ├── accrual_calculator.py    # Accrual-specific logic
│   │   ├── outlook_generator.py     # Outlook-specific logic
│   │   └── requirements.txt
│   └── schedule_validator/           # Future: separate validation function
│       └── lambda_handler.py
├── layers/
│   └── capex-common-lib/
│       └── python/
│           ├── schedule_parser.py
│           ├── cost_allocator.py
│           ├── datasphere_io.py
│           ├── validation.py
│           └── config.py
└── tests/
    ├── test_schedule_parser.py
    ├── test_cost_allocator.py
    └── test_validation.py
```

#### **Testing Strategy**

Each shared module has comprehensive unit tests:
- **schedule_parser**: Test various CSV/Excel formats, handle errors
- **cost_allocator**: Test cost distribution logic, edge cases
- **datasphere_io**: Mock database connections, test error handling
- **validation**: Test all validation rules

---

### **6.4 CI/CD Pipeline & Testing Automation**

#### **Continuous Integration**

Use **GitHub Actions** or **AWS CodePipeline** for automated testing and deployment:

**Pipeline Stages**:

1. **Code Commit** → Triggers pipeline
2. **Unit Testing**
   - Run pytest on all shared modules
   - Test coverage target: >80%
   - Tests must pass before deployment
3. **Integration Testing**
   - Test Lambda with mock Datasphere data
   - Validate calculation results against expected outputs
   - Test reconciliation: `Total Forecast = ITD + Accrual + Outlook`
4. **Linting & Code Quality**
   - Run pylint/flake8 for code standards
   - Check for security vulnerabilities (bandit)
5. **Build Lambda Package**
   - Package code + dependencies
   - Create deployment artifact
6. **Deploy to Dev**
   - Automatic deployment to dev environment
   - Run smoke tests
7. **Deploy to Prod** (manual approval required)
   - After dev validation, deploy to production
   - Tag release with version number

#### **Automated Validation Tests**

Critical tests that run on every calculation:

| Test | Validation Logic | Action on Failure |
|------|------------------|-------------------|
| **Reconciliation Check** | `SUM(Accrual + Outlook + ITD) = SUM(Total_Forecast)` | Fail run, alert team |
| **No Negative Accruals** | `Accrual >= -threshold` (small negative OK) | Flag for review |
| **All WBS Accounted** | All active WBS have forecast records | Log missing WBS |
| **Variance Threshold** | Change vs prior run < 50% (unless schedule change) | Warn if large swing |
| **Data Completeness** | No NULL values in critical fields | Fail affected records |
| **Template Coverage** | All wells have applicable cost template | Flag missing templates |

#### **Deployment Documentation**

Auto-generated documentation on each deployment:
- Git commit hash and message
- Code changes since last version
- Test results summary
- Deployment timestamp
- Deployed by (user)

Stored in S3 and linked to each `Calculation_Version` in database.

#### **Rollback Process**

If production calculation fails:
1. Revert Lambda to previous version (1-click rollback)
2. Preserve failed run logs for debugging
3. Alert assigned on-call developer
4. Forecast uses prior day's results until fixed
5. Post-mortem review before next deployment

---

## **7. Data Models & Schema**

### **7.1 Datasphere Table Structures**

#### **Table: `WBS_Master`**

Master list of WBS elements (wells and projects)

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `WBS_ID` | NVARCHAR(24) | PK - WBS element ID | SAP S/4HANA |
| `WBS_Description` | NVARCHAR(100) | Well or project name | SAP |
| `Business_Unit` | NVARCHAR(10) | BU code | SAP |
| `Basin` | NVARCHAR(50) | Geographic basin | SAP |
| `Project_Type` | NVARCHAR(20) | D&C, Facility, Maint, Misc | SAP |
| `AFE_Number` | NVARCHAR(20) | Authorization for Expenditure | SAP |
| `Estimated_Total_Cost` | DECIMAL(15,2) | AFE budget amount | SAP |
| `In_Service_Date` | DATE | Expected completion | SAP |
| `Created_Date` | DATE | Project creation date | SAP |
| `Status` | NVARCHAR(10) | Active, Complete, Cancelled | SAP |
| `Cost_Center` | NVARCHAR(10) | FK to Cost_Center_Master | SAP |

---

#### **Table: `Cost_Center_Master`**

Cost center hierarchy for management reporting and rollups

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `Cost_Center` | NVARCHAR(10) | PK - Cost center code | SAP S/4HANA |
| `Cost_Center_Name` | NVARCHAR(100) | Cost center description | SAP |
| `Business_Unit` | NVARCHAR(10) | FK to BU_Hierarchy | SAP |
| `Basin` | NVARCHAR(50) | Geographic basin | SAP |
| `Controlling_Area` | NVARCHAR(4) | SAP controlling area | SAP |
| `Company_Code` | NVARCHAR(4) | SAP company code | SAP |
| `Status` | NVARCHAR(10) | Active, Inactive | SAP |

---

#### **Table: `BU_Hierarchy`**

Business unit organizational hierarchy for consolidated reporting

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `Business_Unit` | NVARCHAR(10) | PK - BU code | SAP / Master Data |
| `BU_Name` | NVARCHAR(100) | Business unit name | Master Data |
| `Region` | NVARCHAR(50) | Geographic region | Master Data |
| `Division` | NVARCHAR(50) | Corporate division | Master Data |
| `BU_Lead` | NVARCHAR(100) | BU controller name | Master Data |
| `BU_Email` | NVARCHAR(100) | Contact email | Master Data |
| `Active` | BOOLEAN | Active/inactive flag | Master Data |

---

#### **Table: `SAP_ITD_Actuals`** (Remote Table from S/4HANA)

Incurred-to-date costs from ACDOCA

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `WBS_ID` | NVARCHAR(24) | FK to WBS_Master | ACDOCA |
| `Cost_Element` | NVARCHAR(10) | SAP cost element | ACDOCA |
| `Cost_Category` | NVARCHAR(20) | Drill, Completion, Hookup, Elec | Derived |
| `Posting_Date` | DATE | Transaction date | ACDOCA |
| `Fiscal_Period` | NVARCHAR(7) | YYYY.MM | ACDOCA |
| `Amount` | DECIMAL(15,2) | Cost amount (LC) | ACDOCA |
| `Currency` | NVARCHAR(3) | USD | ACDOCA |

**Calculation View**: `CV_ITD_Summary`
```sql
SELECT
    WBS_ID,
    Cost_Category,
    SUM(Amount) as ITD_Amount
FROM SAP_ITD_Actuals
GROUP BY WBS_ID, Cost_Category
```

---

#### **Table: `Drill_Schedule`**

Drilling activity schedule by well

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `WBS_ID` | NVARCHAR(24) | FK to WBS_Master | BU Operations |
| `Well_Name` | NVARCHAR(100) | Well identifier | Operations |
| `Business_Unit` | NVARCHAR(10) | BU code | Operations |
| `Spud_Date` | DATE | Drilling start date | Operations |
| `Drill_End_Date` | DATE | Drilling completion | Operations |
| `Well_Type` | NVARCHAR(20) | Well classification (Horizontal, Vertical, etc.)* | Operations |
| `Frac_Type` | NVARCHAR(30) | Completion method (Zipper, Plug-and-Perf, etc.)* | Operations |
| `Rig_Name` | NVARCHAR(50) | Drilling rig | Operations |
| `Estimated_Drill_Days` | INTEGER | Days to drill | Operations |
| `Upload_Date` | TIMESTAMP | File upload timestamp | System |
| `Upload_Source` | NVARCHAR(100) | S3 file path | System |

*\*`Well_Type` and `Frac_Type` are descriptive dimensions for v1. Used for reporting segmentation; optionally refine cost template selection when granular templates are available.*

---

#### **Table: `Frac_Schedule`**

Completion and hookup schedule

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `WBS_ID` | NVARCHAR(24) | FK to WBS_Master | BU Operations |
| `Well_Name` | NVARCHAR(100) | Well identifier | Operations |
| `Business_Unit` | NVARCHAR(10) | BU code | Operations |
| `Frac_Start_Date` | DATE | Completion start | Operations |
| `Frac_End_Date` | DATE | Completion end | Operations |
| `Hookup_Date` | DATE | Hookup month | Operations |
| `First_Production_Date` | DATE | Well online date | Operations |
| `Frac_Type` | NVARCHAR(30) | Completion method (Zipper, Plug-and-Perf, etc.)* | Operations |
| `Frac_Crew` | NVARCHAR(50) | Crew identifier | Operations |
| `Upload_Date` | TIMESTAMP | File upload timestamp | System |
| `Upload_Source` | NVARCHAR(100) | S3 file path | System |

*\*`Frac_Type` is a descriptive dimension for v1, used for reporting segmentation.*

---

#### **Table: `WIP_Estimates`**

Value of Work estimates submitted monthly

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `WBS_ID` | NVARCHAR(24) | FK to WBS_Master | SAC Form |
| `Fiscal_Period` | NVARCHAR(7) | YYYY.MM | SAC Form |
| `Cost_Category` | NVARCHAR(20) | Drill, Completion, Hookup, Elec | SAC Form |
| `WIP_Amount` | DECIMAL(15,2) | Estimated work done | Planning Form |
| `Comments` | NVARCHAR(500) | User notes | SAC Form |
| `Submitted_By` | NVARCHAR(50) | User ID | System |
| `Submitted_Date` | TIMESTAMP | Submission timestamp | System |
| `Approval_Status` | NVARCHAR(10) | Pending, Approved | Workflow |

---

#### **Table: `Cost_Templates`**

Standard cost rates per well type and phase

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `Template_ID` | NVARCHAR(20) | PK - Template identifier | Finance/Eng |
| `Basin` | NVARCHAR(50) | Basin applicability | Finance/Eng |
| `Well_Type` | NVARCHAR(20) | Horizontal, Vertical, etc. | Finance/Eng |
| `Cost_Category` | NVARCHAR(20) | Drill, Completion, Hookup, Elec | Finance/Eng |
| `Standard_Cost` | DECIMAL(15,2) | Base cost amount | Finance/Eng |
| `Adjustment_Factor` | DECIMAL(5,4) | Multiplier (e.g., 1.15 for 15% premium) | Finance/Eng |
| `Effective_Date` | DATE | Version start date | Finance/Eng |
| `Expiry_Date` | DATE | Version end date | Finance/Eng |
| `Notes` | NVARCHAR(500) | Template description | Finance/Eng |

---

#### **Table: `Forecast_Results`**

Calculated accruals and outlook (Lambda output)

| Column Name | Data Type | Description | Source |
|-------------|-----------|-------------|--------|
| `WBS_ID` | NVARCHAR(24) | FK to WBS_Master | Lambda |
| `Fiscal_Period` | NVARCHAR(7) | YYYY.MM | Lambda |
| `Cost_Category` | NVARCHAR(20) | Drill, Completion, Hookup, Elec | Lambda |
| `Forecast_Type` | NVARCHAR(10) | Accrual or Outlook | Lambda |
| `Amount` | DECIMAL(15,2) | Forecast amount | Lambda |
| `ITD_Amount` | DECIMAL(15,2) | Reference ITD | Lambda |
| `WIP_Amount` | DECIMAL(15,2) | Reference WIP (for accrual) | Compute |
| `Calculation_Date` | DATE | Run date | Lambda |
| `Calculation_Version` | NVARCHAR(20) | Lambda code version (Git commit hash) | Lambda |
| `Calculation_Run_ID` | NVARCHAR(36) | Unique run identifier (UUID) | Lambda |
| `Input_Version_ID` | NVARCHAR(50) | Hash of input data versions | Lambda |
| `Schedule_File_Timestamp` | TIMESTAMP | Timestamp of schedule file used | Lambda |
| `Cost_Template_Version` | NVARCHAR(20) | Cost template version used | Lambda |
| `Validation_Status` | NVARCHAR(20) | Pass, Fail, Warning | Lambda |
| `Validation_Notes` | NVARCHAR(500) | Validation check results | Lambda |
| `Variance_vs_Prior_Run` | DECIMAL(15,2) | Change from previous calculation | Lambda |

**Calculation View**: `CV_Forecast_Monthly`
```sql
SELECT
    WBS_ID,
    Fiscal_Period,
    Cost_Category,
    SUM(CASE WHEN Forecast_Type = 'Accrual' THEN Amount ELSE 0 END) as Accrual,
    SUM(CASE WHEN Forecast_Type = 'Outlook' THEN Amount ELSE 0 END) as Outlook,
    MAX(ITD_Amount) as ITD
FROM Forecast_Results
WHERE Calculation_Date = (SELECT MAX(Calculation_Date) FROM Forecast_Results)
GROUP BY WBS_ID, Fiscal_Period, Cost_Category
```

---

### **7.2 Data Relationships**

```
WBS_Master (1) ──────────── (M) SAP_ITD_Actuals
    │                              │
    ├──────────── (M) Drill_Schedule
    │                              │
    ├──────────── (M) Frac_Schedule
    │                              │
    ├──────────── (M) WIP_Estimates
    │                              │
    └──────────── (M) Forecast_Results

Cost_Templates (M) ──────────── (1) Basin / Well_Type (lookup)
```

---

## **8. Integration Patterns**

### **8.1 S/4HANA → Datasphere (ITD Actuals)**

**Method**: Live Remote Table Connection

**Frequency**: Real-time (on-demand queries)

**Source**: ACDOCA table in S/4HANA

**Process**:
1. Datasphere maintains live connection to S/4HANA
2. `SAP_ITD_Actuals` is a remote table (virtual)
3. Calculation views query in real-time
4. Lambda reads from calculation view (aggregated data)

**Advantages**:
- Always current data
- No data replication lag
- Single source of truth

---

### **8.2 S3 → Datasphere (Schedules)**

**Method**: Scheduled Data Flow

**Frequency**: Daily at 5:00 AM (before Lambda runs)

**File Format**: CSV or Excel

**S3 Structure**:
```
s3://capex-forecasting/
  ├── drill-schedules/
  │   ├── BU1_Drill_2025-01-09.csv
  │   ├── BU2_Drill_2025-01-09.csv
  │   └── archive/
  ├── frac-schedules/
  │   ├── BU1_Frac_2025-01-09.csv
  │   └── archive/
  └── cost-templates/
      └── Templates_Q1_2025.xlsx
```

**Datasphere Flow**:
1. **Source**: S3 bucket (CSV file)
2. **Transformation**:
   - Validate date formats
   - Check for duplicate WBS
   - Standardize BU codes
3. **Target**: Truncate and load `Drill_Schedule` / `Frac_Schedule`

**Error Handling**:
- Invalid dates → Flag and exclude row
- Missing WBS → Log error, notify BU
- Duplicate wells → Keep latest by upload timestamp

---

### **8.3 Planning → Data Platform (WIP Estimates)**

**Method**: Planning Model Writeback

**Frequency**: Real-time as users enter data

**Process**:
1. Planning model backed by data platform table `WIP_Estimates`
2. Users enter WIP by WBS and month in a form
3. Data written directly to Datasphere via planning model
4. Approval workflow (optional) before data is final

**Planning Model Dimensions**:
- WBS (from `WBS_Master`)
- Fiscal Period
- Cost Category
- Version (Submitted, Approved)

---

### **8.4 Lambda → Datasphere (Forecast Results)**

**Method**: ODBC/JDBC Writeback

**Frequency**: Daily at 6:00 AM (after data refresh)

**Process**:
1. Lambda connects to Datasphere via JDBC
2. Executes truncate: `DELETE FROM Forecast_Results WHERE Calculation_Date = CURRENT_DATE`
3. Bulk insert accrual and outlook records
4. Commit transaction
5. Log row counts and validation checks

**Connection String**:
```python
conn_string = (
    f"Driver={{ODBC Driver 17 for SQL Server}};"
    f"Server={DATASPHERE_HOST};"
    f"Database={DATASPHERE_SPACE};"
    f"UID={USERNAME};"
    f"PWD={PASSWORD};"
)
```

**Error Handling**:
- Connection failure → Retry 3 times with exponential backoff
- Write failure → Rollback, alert team, preserve prior day's results
- Partial success → Log issue, flag affected WBS for manual review

---

### **8.5 Datasphere → SAC (Reporting)**

**Method**: Live Datasphere Connection

**Frequency**: Real-time (on-demand)

**Process**:
1. SAC stories use live connection to Datasphere
2. Queries hit calculation views (`CV_Forecast_Monthly`, `CV_Variance_Analysis`)
3. No data replication needed
4. Users see latest data as of last Lambda run

**Performance Optimization**:
- Calculation views pre-aggregate data
- SAC queries use filters (BU, date range)
- Cached queries for common dashboard views

---

### **8.6 Datasphere Security & Performance**

#### **Security Configuration**

**Row-Level Security (RLS)**

Implement row-level security to ensure users only see authorized data:

| Role | Access Level | Implementation |
|------|--------------|----------------|
| **BU Controller** | Own BU data only | Filter: `Business_Unit = @USER_BU` |
| **Finance Analyst** | Multiple BUs | Filter: `Business_Unit IN @USER_BU_LIST` |
| **Corporate Finance** | All BUs | No filter (full access) |
| **Operations** | Own BU, read-only | Filter: `Business_Unit = @USER_BU` + read-only role |
| **Executives** | All BUs, summary level | Access via executive calculation views |

**Implementation**:
- Configure security in Datasphere Space settings
- Map SAP S/4HANA authorization objects to Datasphere roles
- Use analytic privileges for calculation views
- Test with real user accounts before production

**Column-Level Security**

Restrict sensitive financial data:
- Cost rates and templates: Finance-only access
- Vendor information: Controlled access
- Budget vs actual variances: Controller+ access

**Audit Trail**

- All Datasphere table access logged automatically
- WIP submissions tracked with user ID and timestamp
- Calculation runs logged with version and inputs
- SAC access tracked via SAP analytics

---

#### **Performance Tuning**

**Calculation View Optimization**

Create dedicated aggregated views for SAC dashboards:

```sql
-- CV_Forecast_Summary_BU (Executive Dashboard)
-- Pre-aggregates to BU level for fast loading
SELECT
    Business_Unit,
    Fiscal_Period,
    SUM(CASE WHEN Forecast_Type = 'Accrual' THEN Amount ELSE 0 END) as Total_Accrual,
    SUM(CASE WHEN Forecast_Type = 'Outlook' THEN Amount ELSE 0 END) as Total_Outlook,
    SUM(ITD_Amount) as Total_ITD
FROM Forecast_Results
WHERE Calculation_Run_ID = (SELECT MAX(Calculation_Run_ID) FROM Forecast_Results)
GROUP BY Business_Unit, Fiscal_Period
```

**Indexing Strategy**:
- Primary keys: `WBS_ID`, `Business_Unit`, `Fiscal_Period`
- Composite indexes: `(Business_Unit, Fiscal_Period)`, `(WBS_ID, Calculation_Run_ID)`
- Foreign keys indexed for join performance

**Query Performance Targets**:
- Executive dashboard: < 3 seconds
- BU detail view: < 5 seconds
- Well-level drill-down: < 8 seconds
- Export queries: < 15 seconds

**Monitoring**:
- Datasphere query monitor for slow queries
- SAC performance analytics
- Weekly performance review during Phase 4-5
- Optimize top 10 slowest queries

**Data Volume Management**:
- Archive calculation runs older than 24 months
- Retain only latest calculation per day (delete interim runs)
- Partition large tables by Fiscal_Period
- Estimated growth: ~50K records/month

---

## **9. Timeline & Milestones**

### **9.1 Gantt Chart Overview**

```
Weeks:        1   2   3   4   5   6   7   8   9   10  11  12  13  14  15  16
             ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Phase 1      ███████████████
Phase 2              ███████████████
Phase 3                      ███████████████████████████
Phase 4                                      ███████████████████
Phase 5                                          ███████████████████████
Phase 6                                                      ███████████████████

Milestones:
  ▼ Week 3: Datasphere data model complete
      ▼ Week 5: Data ingestion pipelines operational
            ▼ Week 9: Lambda calculation engine validated
                  ▼ Week 11: SAC reports launched
                        ▼ Week 13: Pilot BU sign-off
                              ▼ Week 16: Production go-live
```

### **9.2 Key Milestones**

| Week | Milestone | Deliverable | Gate Criteria |
|------|-----------|-------------|---------------|
| **3** | Data Foundation Complete | Datasphere schema + S/4HANA connection | - All tables created<br>- ITD data flowing<br>- Data dictionary approved |
| **5** | Data Ingestion Operational | Object Storage → Data Platform + WIP forms | - Schedule files loading routinely<br>- WIP form functional<br>- Data validation working |
| **9** | Calculation Engine Validated | Lambda producing forecasts | - Accruals match manual calc<br>- Outlook logic approved<br>- Unit tests passing |
| **11** | SAC Reports Launched | All 4 core reports live | - Reports load < 5 sec<br>- User navigation tested<br>- Finance SME approval |
| **13** | Pilot BU Sign-Off | UAT complete, reconciled | - Calculations reconciled<br>- Users trained<br>- Monthly close successful |
| **16** | Production Go-Live | All BUs operational | - All BUs migrated<br>- Support processes live<br>- Monitoring active |

---

### **9.3 Critical Path**

The following items are on the critical path and cannot be delayed:

1. **S/4HANA Connection** (Week 2) → Blocks ITD data availability
2. **Calculation Logic Approval** (Week 7) → Blocks Lambda development completion
3. **Pilot BU Validation** (Week 12) → Blocks production rollout
4. **Production Deployment** (Week 14) → Blocks BU onboarding

**Buffer**: 2 weeks built into 16-week timeline for contingencies

---

## **10. Risks & Mitigation Strategies**

### **10.1 Risk Register**

| Risk ID | Risk Description | Probability | Impact | Mitigation Strategy | Owner |
|---------|------------------|-------------|--------|---------------------|-------|
| **R1** | S/4HANA connection performance issues | Medium | High | - Pre-aggregate data in calc views<br>- Schedule off-peak query times<br>- Consider delta extraction | SAP Team |
| **R2** | Schedule file format inconsistencies across BUs | High | Medium | - Define strict file standard<br>- Build robust validation logic<br>- Provide BU file templates | Data Science |
| **R3** | Calculation logic disputes with Finance | Medium | High | - Early and frequent validation sessions<br>- Document all assumptions<br>- Side-by-side comparison reports | Finance SMEs |
| **R4** | WIP data entry adoption resistance | Medium | Medium | - Simplify form design<br>- Provide training<br>- Show value through reporting | Fin Reporting |
| **R5** | Lambda timeout for large datasets | Low | High | - Optimize pandas operations<br>- Increase memory/timeout<br>- Implement batching | Data Science |
| **R6** | Datasphere space storage limits | Low | Medium | - Archive historical data quarterly<br>- Monitor space usage<br>- Request capacity increase | SAP Team |
| **R7** | Integration failures between systems | Medium | High | - Implement retry logic<br>- Comprehensive error logging<br>- Alerting to on-call team | Data Science |
| **R8** | Cost template update delays | Low | Medium | - Quarterly review cadence<br>- Template versioning<br>- Alert when templates expire | Finance SMEs |
| **R9** | User security and access issues | Medium | Low | - Define roles early<br>- Test with real user IDs<br>- Document access request process | SAP Team |
| **R10** | Lack of cross-team coordination | Medium | High | - Weekly standup meetings<br>- Shared project tracker<br>- Clear RACI matrix | Project Lead |

---

### **10.2 Data Quality Controls**

| Control Point | Check | Action on Failure |
|---------------|-------|-------------------|
| **ITD Actuals** | Compare WBS count to prior day | Alert if variance > 10% |
| **Drill Schedule** | Validate all dates are future or recent past | Flag invalid rows, notify BU |
| **Frac Schedule** | Check Frac Start >= Drill End for same well | Flag for review |
| **WIP Estimates** | WIP should be <= AFE budget | Warn user, allow override |
| **Cost Templates** | No gaps in effective date coverage | Alert Finance before month-end |
| **Forecast Results** | Total Forecast = ITD + Accrual + Outlook | Fail Lambda run if mismatch |
| **ITD vs Template** | ITD < Template Cost for each phase | If ITD >= Template: Set Outlook = $0, flag as `OVERRUN_REVIEW`, escalate to Finance |
| **Schedule Date Validity** | Phase End >= Phase Start | If invalid: Flag as `INVALID_SCHEDULE`, exclude from Outlook, notify BU |
| **Missing Schedule** | All active WBS have schedule dates | If missing: Use `estimate_missing_schedule()` to impute from similar wells, flag as `ESTIMATED_SCHEDULE` |
| **Allocation Reconciliation** | Sum of monthly allocations = Total Phase Outlook | Log warning if difference > $1 (rounding) |

---

## **11. Success Criteria & KPIs**

### **11.1 Success Metrics**

#### **Accuracy & Quality**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Accrual Accuracy** | 95% match to manual calculations | Variance < 5% for pilot BU |
| **Forecast Variance** | Outlook within 10% of actuals (3-month lag) | Track actual vs prior outlook |
| **Data Reconciliation** | 100% ITD match to SAP | Monthly reconciliation report |
| **Error Rate** | < 1% of records flagged | % of wells with validation errors |

#### **Performance**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Lambda Execution Time** | < 3 minutes | CloudWatch logs |
| **SAC Report Load** | < 5 seconds | User experience testing |
| **Data Freshness** | Daily by 8 AM | Monitoring dashboard |
| **System Uptime** | 99%+ | AWS/SAP monitoring |

#### **Adoption**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **WIP Submission Rate** | Target % of active wells by period end | Completion tracking |
| **User Logins** | 80%+ of licensed users active monthly | SAC analytics |
| **Training Completion** | 100% of key users | Training tracker |
| **User Satisfaction** | 4+ / 5 rating | Post-implementation survey |

#### **Efficiency**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Time Savings** | 50% reduction in manual forecast prep time | User survey |
| **Monthly Close** | Accrual file ready by Day 2 | Process tracking |
| **Schedule Update Lag** | < 1 day from operational change to forecast update | Timestamp tracking |

---

### **11.2 Go-Live Readiness Checklist**

**Technical Readiness**
- [ ] All data integrations tested and validated
- [ ] Lambda function deployed to production
- [ ] SAC reports accessible to all users
- [ ] Monitoring and alerting configured
- [ ] Backup and recovery procedures tested
- [ ] Security roles and permissions configured

**Data Readiness**
- [ ] All BUs' historical data loaded
- [ ] Current drill and frac schedules uploaded
- [ ] Cost templates reviewed and approved
- [ ] ITD actuals reconciled to SAP

**User Readiness**
- [ ] All users trained
- [ ] User guides and documentation available
- [ ] Help desk process established
- [ ] Power users identified per BU

**Process Readiness**
- [ ] Monthly close calendar updated
- [ ] WIP submission deadline communicated
- [ ] Governance committee established
- [ ] Change request process defined

**Business Readiness**
- [ ] Finance SME sign-off on calculations
- [ ] Pilot BU successfully completed 2 monthly closes
- [ ] Variance explanations documented
- [ ] Executive stakeholders briefed

---

## **12. Future Roadmap**

### **12.0 v1 Assumptions (Intentionally Simplified)**

The following design decisions are intentionally simplified for v1 to reduce complexity and accelerate delivery. These are documented for transparency and may evolve in future versions:

| Area | v1 Approach | Rationale | Future Enhancement |
|------|-------------|-----------|-------------------|
| **Cost Allocation** | Linear by Day | Simple, transparent, auditable | S-curve based on historical spend patterns |
| **Cost Templates** | Single template per basin/well type | Sufficient for 80% of wells | Depth/complexity adjustments |
| **Missing Schedules** | Average from similar wells | Practical heuristic | ML-based prediction |
| **Overrun Handling** | Manual review required | Finance control over estimates | Automatic re-forecasting |
| **Granularity** | Monthly reporting | Matches finance cadence | Weekly/daily visibility |
| **Uncertainty** | Deterministic forecast | Simpler to explain | Probabilistic ranges |

**Key v1 Constraints**:
1. **No S-curve allocation** - All phases use linear distribution
2. **No stage-count weighting** - Completions allocated by days, not frac stages
3. **No ML predictions** - Imputation uses simple averages
4. **No automatic overrun adjustment** - ITD >= Template requires manual intervention
5. **No confidence intervals** - Single point estimate only

### **12.1 Phase 2 Enhancements (Months 4-6)**

**Expand to Additional CapEx Categories**
- Facility Projects forecasting
- Maintenance Projects (sustaining capital)
- Miscellaneous Projects

**Advanced Features**
- Scenario planning (optimistic/pessimistic forecasts)
- What-if analysis for schedule changes
- Automated variance explanations (AI-generated)

**Integration Enhancements**
- Real-time schedule updates (API instead of file drops)
- Automated AFE budget pulls from project management system
- Integration with procurement for vendor cost actuals

**Infrastructure Enhancements** (As Needed for Scale)

These enhancements are not required for MVP but should be considered as data volume grows:

**1. API Gateway Layer**

**When to Implement**: When moving from daily batch to real-time/event-driven updates

**Benefits**:
- Event-driven architecture: Schedule change triggers immediate forecast update
- Better error handling and retry logic
- API versioning for controlled changes
- Rate limiting and throttling
- Centralized logging and monitoring

**Architecture**:
```
Schedule Upload → S3 → EventBridge → API Gateway → Lambda → Datasphere
```

**Implementation**:
- Create REST API in AWS API Gateway
- Lambda functions called via API endpoints
- Supports multiple trigger sources (S3, manual calls, other systems)
- Enables future integration with external systems

**Cost**: Minimal (~$5-10/month for expected volume)

**Trigger Point**: When BUs need intra-day forecast updates or volume exceeds 10,000 wells

---

**2. Caching Layer**

**When to Implement**: When SAC dashboard performance degrades (>5,000 wells or >100 concurrent users)

**Benefits**:
- Sub-second dashboard load times
- Reduced Datasphere query load
- Better user experience during peak times (month-end)

**Options**:

| Option | Use Case | Cost | Complexity |
|--------|----------|------|------------|
| **S3 Parquet Cache** | Batch refresh, simple queries | Low ($5/mo) | Low |
| **Redis/ElastiCache** | Real-time, high concurrency | Medium ($50/mo) | Medium |
| **SAC Cached Models** | Native SAC caching | Included | Low |

**Recommended Approach**: Start with SAC cached models, move to S3 Parquet if needed

**Architecture**:
```
Lambda → Datasphere (write) → Also writes summary to S3 Parquet
SAC Dashboard → Reads from S3 Parquet (fast) for summary views
SAC Drill-Down → Reads from Datasphere (detail views)
```

**Trigger Point**:
- Dashboard load time consistently > 8 seconds
- Concurrent users > 100
- Well count > 5,000

---

**3. Data Service Layer** (Optional)

**When to Implement**: When multiple downstream systems need forecast data

**Purpose**: Centralized API for forecast data access

**Architecture**:
```
Datasphere ← Lambda (writes)
    ↓
Data Service API (AWS Lambda + API Gateway)
    ↓
    ├─→ SAC (reporting)
    ├─→ Power BI (if needed)
    ├─→ Other Finance Systems
    └─→ External APIs
```

**Benefits**:
- Single point of data access control
- Consistent data format across consumers
- Easier to version and change backend without breaking consumers
- Better audit trail of who accessed what

**Trigger Point**: When 3+ systems need forecast data

---

### **12.2 Phase 3: OpEx Forecasting (Months 7-12)**

**Driver-Based OpEx Model**

Similar framework applied to Operating Expenses:

**Potential Drivers**:
- Active well count → LOE (Lease Operating Expense)
- Production volumes (BOE) → Gathering & Transportation
- Power consumption (kWh) → Electricity costs
- Headcount → Labor costs
- Chemical usage → Treating costs

**Data Sources**:
- Production system for well counts and volumes
- IoT sensors for power consumption
- HR system for headcount
- ERP for vendor invoices (actuals)

**Calculation Logic**:
```
OpEx Forecast = Driver Volume × Unit Rate
```

Example:
```
Electricity Forecast = (Active Wells × Avg kWh per Well × Rate per kWh)
```

---

### **12.3 Machine Learning Integration (Months 13-18)**

**Predictive Cost Models**

Partner with Centralized AI Team to develop:

1. **Drilling Time Prediction**
   - Model: XGBoost regression
   - Features: Basin, depth, formation, rig type, historical performance
   - Output: Predicted drill days (refines outlook timing)

2. **Cost Overrun Prediction**
   - Model: Classification (high/medium/low risk)
   - Features: Project complexity, vendor, weather, schedule variance
   - Output: Risk score for budget overruns

3. **Well Performance Forecasting**
   - Model: Time series (LSTM)
   - Features: Geology, completion design, offset well performance
   - Output: Expected production curve (informs revenue forecast)

**Hybrid Model**:
- **Driver-based** provides explainable baseline
- **ML models** provide refinement and risk assessment
- Finance can override ML predictions if needed

---

### **12.4 Long-Term Vision (18+ Months)**

**Integrated Capital Lifecycle Reporting**
- AFE → Forecast → Actuals → Post-completion analysis
- Automated project close-out and lessons learned

**Predictive Analytics Dashboard**
- AI-flagged cost variances before they occur
- Recommended schedule optimizations
- Basin-level cost benchmarking

**SAC Planning Integration**
- Unified CapEx and OpEx planning model
- Rolling 18-month forecasts with driver adjustments
- Board-ready reporting and executive summaries

**ERP Integration**
- Automated accrual posting to S/4HANA
- Purchase requisition forecasting
- Cash flow forecasting linked to capital plan

---

## **Appendices**

### **Appendix A: Glossary**

| Term | Definition |
|------|------------|
| **AFE** | Authorization for Expenditure - Approved budget for a capital project |
| **ACDOCA** | SAP Universal Journal table containing all financial postings |
| **D&C** | Drilling & Completions |
| **ITD** | Incurred-to-Date - Actual costs posted to SAP to date |
| **WIP** | Work-in-progress - Operational estimate of work completed but not yet invoiced |
| **WBS** | Work Breakdown Structure - Project identifier in SAP |
| **BU** | Business Unit |
| **Accrual** | Cost for work completed but not yet invoiced (WIP - ITD) |
| **Outlook** | Forward-looking forecast for future costs |
| **Spud** | Drilling start date |
| **Frac** | Hydraulic fracturing / well completion |

### **Appendix B: Contact Matrix**

| Role | Name | Email | Responsibility |
|------|------|-------|----------------|
| Project Sponsor | [TBD] | [TBD] | Executive oversight |
| Finance SME Lead | [TBD] | [TBD] | Business requirements |
| Finance Reporting Lead | [TBD] | [TBD] | Datasphere & SAC |
| Data Science Lead | [TBD] | [TBD] | Lambda development |
| SAP Team Lead | [TBD] | [TBD] | Infrastructure & security |
| AI Team Advisor | [TBD] | [TBD] | Architecture review |

### **Appendix C: Reference Documents**

- Project Overview Brief (this document's source)
- Datasphere Data Dictionary
- Lambda Function API Documentation
- SAC User Guide
- Monthly Close Process Guide
- Cost Template Methodology

---

### **Appendix D: AWS Cloud Governance & Cost Control**

#### **D.1 Resource Tagging Policy**

All AWS resources must be tagged with standardized tags for cost tracking, governance, and ownership:

**Mandatory Tags**:

| Tag Name | Description | Example Value |
|----------|-------------|---------------|
| `Project` | Project identifier | `capex-forecasting` |
| `Environment` | Environment type | `dev`, `test`, `prod` |
| `Owner` | Team owning the resource | `data-science-team` |
| `CostCenter` | Finance cost center | `IT-DataScience-001` |
| `Application` | Application name | `forecast-calculator` |
| `ManagedBy` | Management method | `terraform`, `manual` |
| `DataClassification` | Data sensitivity | `confidential`, `internal` |
| `BackupPolicy` | Backup requirement | `daily`, `none` |

**Implementation**:
- Enforce via AWS Config rules (resources without tags flagged)
- Tag compliance report monthly
- Cost allocation reports by Project, CostCenter, Environment

**Resource Inventory**:

| Resource Type | Resource Name | Environment | Monthly Cost |
|---------------|---------------|-------------|--------------|
| Lambda Function | `capex_forecast_calculator` | prod | $8 |
| Lambda Layer | `capex-common-lib` | prod | $0 |
| S3 Bucket | `capex-forecasting-schedules` | prod | $3 |
| S3 Bucket | `capex-forecasting-archive` | prod | $1 |
| EventBridge Rule | `daily-forecast-trigger` | prod | $0 |
| CloudWatch Logs | Lambda execution logs | prod | $2 |
| **Total Estimated** | | | **~$14/month** |

---

#### **D.2 Cost Monitoring & Budget Alerts**

**CloudWatch Budget Alarms**:

| Budget Name | Threshold | Alert Action |
|-------------|-----------|--------------|
| `capex-forecast-monthly` | $20/month | Email to Data Science Lead + Finance |
| `capex-forecast-quarterly` | $60/quarter | Email + Slack notification |
| `lambda-execution-anomaly` | 50% increase vs prior week | Alert DevOps team |

**Cost Optimization**:
- Lambda memory tuning: Right-size based on execution metrics
- S3 lifecycle policies: Move archived schedules to Glacier after 90 days
- CloudWatch log retention: 30 days for dev, 90 days for prod
- Reserved capacity: Consider reserved Datasphere capacity if usage grows

**Monthly Cost Review**:
- Review AWS Cost Explorer dashboard
- Compare actual vs budgeted costs
- Identify top 3 cost drivers
- Report to steering committee

---

#### **D.3 Security & Access Control**

**IAM Roles & Permissions**

**Lambda Execution Role**: `capex-forecast-lambda-role`

Permissions:
- S3: Read schedules from `capex-forecasting-schedules/*`
- Secrets Manager: Read Datasphere credentials
- CloudWatch: Write logs
- **NO** direct user credentials - use IAM roles only

**Datasphere Connection**:
- Store connection string in AWS Secrets Manager
- Lambda retrieves credentials at runtime
- Rotate credentials quarterly
- Use service account, not individual user accounts

**Access Control**:

| Role | AWS Access | Permissions |
|------|------------|-------------|
| **Data Science Developer** | Dev Lambda, Dev S3 | Full access to dev resources, read-only prod |
| **DevOps** | All environments | Deploy, monitor, troubleshoot |
| **Finance SME** | S3 schedule bucket only | Upload schedules, no Lambda access |
| **IT SAP Team** | Secrets Manager, IAM | Manage credentials, security policies |

**Security Best Practices**:
- Enable AWS CloudTrail for audit logging (all API calls)
- Encrypt S3 buckets with AWS KMS
- Enable VPC endpoints for Datasphere connection (no internet routing)
- MFA required for production deployments
- Regular security reviews (quarterly)

---

#### **D.4 Monitoring & Alerting**

**CloudWatch Dashboards**:

Create `CapEx-Forecast-Operations` dashboard with:
- Lambda execution time (p50, p95, p99)
- Lambda error rate
- Datasphere connection errors
- S3 file upload counts by BU
- Daily forecast completion status

**Alarms**:

| Alarm | Condition | Action |
|-------|-----------|--------|
| `forecast-calculation-failure` | Lambda returns error code | Page on-call, email team |
| `forecast-duration-high` | Execution time > 4 minutes | Email performance warning |
| `datasphere-connection-error` | Connection failures > 2 in 1 hour | Email IT SAP team |
| `missing-schedule-file` | Expected BU file not uploaded | Email BU operations |
| `validation-failures-high` | >10% of records fail validation | Email Finance SME |

**On-Call Rotation**:
- Primary: Data Science Team (weekdays)
- Secondary: DevOps (24/7)
- Escalation: IT SAP Team (for Datasphere issues)

---

#### **D.5 Backup & Disaster Recovery**

**Backup Strategy**:

| Component | Backup Method | Frequency | Retention |
|-----------|---------------|-----------|-----------|
| Lambda Code | Git repository + S3 versioning | On each commit | Indefinite |
| Datasphere Tables | Native Datasphere backup | Daily | 30 days |
| Forecast Results | Archived to S3 | Daily post-calculation | 7 years |
| Schedule Files | S3 versioning enabled | On upload | 90 days |
| Cost Templates | Versioned in Datasphere | On update | All versions |

**Recovery Time Objectives (RTO)**:
- Lambda failure: < 1 hour (rollback to previous version)
- Datasphere outage: Use cached results, RTO 4 hours
- Complete system failure: Revert to manual process, RTO 24 hours

**Disaster Recovery Testing**:
- Quarterly DR drill (simulate Lambda failure, test rollback)
- Annual full DR test (simulate Datasphere outage)
- Document lessons learned and update runbooks

---

#### **D.6 Compliance & Audit**

**Audit Requirements**:
- SOX compliance: Audit trail for all forecast changes
- Data retention: 7 years for financial data
- Access reviews: Quarterly review of who has access to what

**Audit-Ready Documentation**:
- Calculation logic documented in Git README
- All code changes tracked with commit messages
- Deployment history in S3 (who deployed what when)
- User access logs in CloudTrail
- Forecast results include calculation version and inputs (lineage)

**Quarterly Audit Deliverables**:
- List of all users with access
- Summary of code changes (Git log)
- Cost variance report (budgeted vs actual AWS spend)
- Security posture review (vulnerabilities, patching status)

---

## **Document Control**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-09 | AI Assistant | Initial development plan created |

**Next Review Date**: Start of Phase 1 (adjust based on actual kickoff)

---

**End of Development Plan**
