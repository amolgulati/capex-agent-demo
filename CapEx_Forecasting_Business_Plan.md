# **CapEx Driver-Based Forecasting**
Architecture note: This document is deliberately generalized for external sharing. Names, timelines, costs, vendor technologies/configurations, governance specifics, and operational cadences have been removed or abstracted. Content represents options and concepts for discussion — not final; details are to be determined.
## Business Plan & Value Proposition

**Prepared For**: Finance Leadership, Business Unit Controllers, Operations Management
**Date**: January 2025
**Timeline**: Indicative phases only; timeline to be determined (TBD)

---

## **Executive Summary**

This initiative will **transform how we forecast capital expenditures** by replacing manual, spreadsheet-driven processes with an automated, driver-based system that ties financial forecasts directly to operational reality.

**The Opportunity**: Our current manual forecasting process creates delays, inconsistencies, and limited visibility into capital spending. By the time we close the month and review variances, operational realities have already shifted.

**The Solution**: An integrated forecasting platform that automatically generates accruals and forward-looking forecasts based on real-time drill and frac schedules, delivering transparency, accuracy, and speed.

**The Impact**:
- **50% reduction** in time spent on manual forecast preparation
- **>90% forecast accuracy** within 3 months of project completion
- **Real-time visibility** into capital commitments across all business units
- **Automated monthly accruals**, eliminating manual calculation errors
- **Scalable foundation** for Facilities, Maintenance, and predictive analytics

---

## **Table of Contents**

1. [Business Problem & Current State](#1-business-problem--current-state)
2. [Solution Overview](#2-solution-overview)
3. [Business Value & Benefits](#3-business-value--benefits)
4. [How It Works](#4-how-it-works)
5. [Implementation Roadmap](#5-implementation-roadmap)
6. [Team Roles & Governance](#6-team-roles--governance)
7. [Change Management & Training](#7-change-management--training)
8. [Success Metrics](#8-success-metrics)
9. [Investment & ROI](#9-investment--roi)
10. [Risks & Mitigation](#10-risks--mitigation)
11. [Strategic Roadmap](#11-strategic-roadmap)

---

## **1. Business Problem & Current State**

### **The Challenge**

Our current capital forecasting process relies on:
- **Manual spreadsheets** maintained separately by each business unit
- **Monthly work-in-progress (WIP) estimates** that require effort to collect and validate
- **Disconnected systems** between operations (schedules) and finance (forecasts)
- **Lagging visibility** - forecasts often trail operational changes by weeks

### **The Impact**

This creates tangible business problems:

| Problem | Impact | Estimated Cost |
|---------|--------|----------------|
| **Manual Accrual Calculation** | Finance team spends time calculating WIP - ITD | Cost in labor |
| **Forecast Inaccuracy** | Variance between forecast and actuals averages 15-20% | Poor capital allocation decisions |
| **Delayed Decision-Making** | Management sees outdated forecasts, hampering real-time capital reallocation | Opportunity cost |
| **Audit Trail Gaps** | Difficulty explaining forecast changes and accrual basis | Compliance risk |
| **BU Inconsistency** | Each BU uses different methods, making consolidation difficult | Executive visibility issues |
| **Schedule Disconnect** | Operations updates drill/frac plans weekly, but forecasts lag behind | Reactive vs proactive planning |

### **The Root Cause**

We lack a **single, automated system** that connects operational drivers (well schedules) to financial forecasts. Finance teams are forced to be data collectors rather than strategic advisors.

---

## **2. Solution Overview**

### **What We're Building**

A **driver-based forecasting platform** that automatically:
1. Pulls actual costs (ITD) from SAP in real-time
2. Calculates monthly accruals based on work-in-progress (WIP) estimates
3. Generates forward-looking forecasts tied to drill and frac schedules
4. Updates forecasts automatically as operations adjust schedules
5. Delivers reports and dashboards through a planning and analytics platform

### **The "Driver-Based" Difference**

Traditional forecasting uses historical trends and extrapolation. **Driver-based forecasting** ties every dollar to a specific operational activity:

- **Drilling costs** → Tied to spud dates and drilling schedules
- **Completion costs** → Tied to frac schedules
- **Hookup & electricity** → Tied to well online dates

When operations changes a schedule, the forecast **automatically updates** - no manual intervention needed.

### **What Makes This Unique**

| Traditional Forecasting | Driver-Based Forecasting (This Solution) |
|------------------------|------------------------------------------|
| Manual spreadsheets per BU | Centralized, automated platform |
| Historical trends + judgment | Operational schedules + cost templates |
| Monthly refresh cycle | Daily automatic updates |
| Difficult to explain variances | Every number traceable to source |
| Inconsistent across BUs | Standardized methodology |
| Finance-only view | Shared visibility with Operations |

### **Technology Foundation**

The solution leverages our existing technology investments:
- **Centralized Data Platform** - Curated source of truth for integrated data
- **ERP System** - Connection to actual costs
- **Planning & Analytics Platform** - Familiar interface for reports and driver entry
- **AWS** - Calculation engine (aligns with existing ML infrastructure)

No new systems for users to learn - finance teams continue using SAC, operations continue managing schedules.

---

## **3. Business Value & Benefits**

### **3.1 Quantified Benefits**

#### **Time Savings**

| Process | Current State | Future State | Time Saved |
|---------|---------------|--------------|------------|
| Monthly accrual calculation | 40-60 hours | 5 hours (review only) | **90% reduction** |
| Forecast preparation | 80 hours/BU/month | 20 hours/BU/month | **75% reduction** |
| Variance analysis | Manual reconciliation | Automated reports | **60% reduction** |
| Schedule change updates | 2-3 days lag | Real-time | **Immediate visibility** |

**Total**: Approximately **500+ hours per month** redirected from data collection to value-added analysis.

#### **Accuracy Improvements**

- **Current state**: 15-20% variance between forecast and actuals at 3-month horizon
- **Target state**: <10% variance within 3 months of project completion
- **Accrual accuracy**: >95% match between calculated and actual invoices

#### **Decision-Making Speed**

- **Current**: Capital reallocation decisions made with 2-4 week old data
- **Future**: Decisions made with previous-day data (refreshed daily at 8 AM)
- **Impact**: Ability to respond to operational changes within hours, not weeks

### **3.2 Strategic Benefits**

#### **For Finance Leadership**

- **Single source of truth** for capital forecasts across all BUs
- **Consistent methodology** enabling apples-to-apples comparisons
- **Audit-ready** - every number traceable to operational driver or SAP actual
- **Scenario planning** capabilities (e.g., "What if we delay these 5 wells?")
- **Foundation for cash flow forecasting** and working capital management

#### **For Business Unit Controllers**

- **Real-time visibility** into BU capital position vs budget
- **Automated variance explanations** tied to schedule changes
- **Reduced month-end stress** with auto-generated accrual files
- **More time for strategic analysis** vs data gathering
- **Consistent reporting** to BU leadership

#### **For Operations**

- **Financial visibility** of their schedule decisions in real-time
- **Collaboration with Finance** on the same data platform
- **Better capital allocation** decisions with financial implications visible
- **Recognition of operational progress** reflected immediately in financial view

#### **For Executive Leadership**

- **Board-ready reporting** with clear explanations and drill-down capability
- **Proactive capital management** - see issues before they become problems
- **Data-driven decisions** on capital allocation across portfolio
- **Confidence in the numbers** with transparent, auditable methodology

### **3.3 Qualitative Benefits**

- **Eliminates finger-pointing** - Operations and Finance work from same schedules
- **Reduces month-end surprises** - continuous visibility vs monthly shock
- **Empowers finance teams** - shift from data entry to strategic advisory
- **Builds trust with stakeholders** - transparent, explainable forecasts
- **Supports growth** - scalable platform can handle expanding well counts
- **Audit-ready data governance** - complete lineage tracking from source to forecast
- **Automated quality controls** - built-in validation and reconciliation checks
- **Enterprise-grade security** - role-based access aligned with existing SAP permissions

---

## **4. How It Works**

### **The Forecasting Formula**

Every capital project (WBS) is broken into three components:

```
Total Forecast = ITD (Actuals) + Accrual (Work Done) + Outlook (Future Work)
```

| Component | What It Means | Where It Comes From |
|-----------|---------------|---------------------|
| **ITD (Incurred-to-Date)** | Costs already booked | Pulled automatically from ERP/source systems |
| **Accrual** | Work completed but not yet invoiced | WIP (work-in-progress) estimate - ITD |
| **Outlook** | Future costs to complete project | Drill/frac schedule × cost templates |

### **How Outlook Dollars Are Spread Across Time**

The system uses a simple, transparent method called **Linear by Day** to allocate forecasted costs to each month:

1. **Calculate a daily rate**: Divide the total phase cost by the number of days in that phase
2. **Assign to months**: Multiply the daily rate by the number of phase days in each month

**Example**: A $300,000 drilling phase lasting 45 days (Jan 15 - Feb 28)
- Daily rate = $300,000 ÷ 45 days = $6,667/day
- January (17 days of drilling): $6,667 × 17 = **$113,333**
- February (28 days of drilling): $6,667 × 28 = **$186,667**

This method ensures:
- **Transparency**: Every dollar can be traced back to specific schedule days
- **Consistency**: All BUs use the same calculation logic
- **Automatic updates**: When schedules change, the allocation recalculates immediately

**Special Cases**:
- **Hookup costs**: Allocated 100% to the hookup month (not spread across days)
- **Overruns**: If actual costs exceed the template, Outlook is set to $0 and flagged for Finance review
- **Missing schedule dates**: System estimates timing based on similar wells in the same basin

### **The Monthly Cycle**

#### **Week 1: Schedule Updates**
1. **Operations** updates drill and frac schedules (as they do today)
2. Schedules automatically flow into the system daily
3. **System** recalculates outlook based on new timing

#### **Week 2-3: WIP Entry**
1. **Operations** submits Value of Work estimates via simple SAC form
   - "How much drilling work was completed this month?"
   - "How much completion work was completed?"
2. **System** calculates accrual: `Accrual = WIP - ITD`
3. **Finance** reviews and approves

#### **Week 4: Month-End Close**
1. **System** generates accrual file automatically
2. **Accounting** books accrual journal entry (1-click process)
3. **Finance** reviews variance reports and outlook
4. **Management** receives dashboards and briefings

#### **Daily: Continuous Visibility**
- Forecasts refresh daily at 6 AM (after schedule files load)
- All users see updated forecasts by 8 AM
- No manual intervention needed

### **Data Flow Diagram**

```
┌─────────────────┐
│  BU OPERATIONS  │
└────────┬────────┘
         │ (Upload schedules to shared location)
         ▼
┌─────────────────┐         ┌─────────────────┐
│  DRILL & FRAC   │         │  ERP / ACTUALS  │
│   SCHEDULES     │────┐    │   (Actuals)     │
└─────────────────┘    │    └────────┬────────┘
                       │             │
                       ▼             ▼
              ┌─────────────────────────────┐
              │    CENTRAL DATA PLATFORM    │
              │  (Curated Source of Truth)  │
              └────────────┬────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │   CALCULATION ENGINE        │
              │  (AWS - Daily at 6 AM)      │
              │                             │
              │  • Calculate Accruals       │
              │  • Generate Outlook         │
              │  • Validate Results         │
              └────────────┬────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │   PLANNING & ANALYTICS      │
              │  (Reports & Dashboards)     │
              │                             │
              │  • Accrual File             │
              │  • Outlook Forecast         │
              │  • Variance Reports         │
              │  • Executive Dashboards     │
              └─────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────────┐
              │   BUSINESS USERS            │
              │  Finance • Ops • Leadership │
              └─────────────────────────────┘
```

### **User Experience**

#### **For Finance Analysts**
- Log into SAC (same tool you use today)
- Dashboard shows current capital position by BU
- Click to drill down to well-level detail
- Export accrual file for month-end booking

#### **For Operations**
- Upload drill/frac schedules to shared folder (or continue using existing process)
- Submit WIP estimates via simple web form
- View financial impact of schedule changes in real-time

#### **For Controllers**
- Access variance reports showing Actual vs WIP vs Outlook
- See which wells drove changes month-over-month
- Prepare management briefings with one-click exports

---

## **5. Implementation Roadmap**

### **5.1 Phased Approach**

We'll deliver value incrementally through six phases over 12-16 weeks:

```
Phase 1: Foundation         Phase 2: Data         Phase 3: Calculations
(Weeks 1-3)                 (Weeks 3-5)          (Weeks 5-9)
├─ Data model setup         ├─ Schedule imports   ├─ Accrual logic
├─ SAP connections          ├─ WIP entry forms    ├─ Outlook engine
└─ Initial data load        └─ Data validation    └─ Testing

Phase 4: Reporting          Phase 5: Pilot        Phase 6: Rollout
(Weeks 8-11)                (Weeks 10-13)         (Weeks 13-16)
├─ Dashboards               ├─ Single BU pilot    ├─ All BUs live
├─ Accrual files            ├─ Reconciliation     ├─ Training
└─ Variance reports         └─ UAT approval       └─ Production
```

### **5.2 Key Milestones**

| Week | Milestone | What It Means for Business |
|------|-----------|----------------------------|
| **Week 3** | Data foundation complete | Data models ready, SAP connection live |
| **Week 5** | Data ingestion operational | Schedules flowing, WIP form working |
| **Week 9** | Calculation engine validated | Accruals and forecasts generating accurately |
| **Week 11** | Reports launched | All dashboards and exports available |
| **Week 13** | Pilot BU sign-off | One BU successfully using system for month-end |
| **Week 16** | Production go-live | All BUs operational, old process retired |

### **5.3 What Happens Each Phase**

#### **Phase 1-2: Behind the Scenes (Weeks 1-5)**
- **You'll see**: Project kickoffs, data model reviews, demo sessions
- **You'll do**: Provide sample data, validate cost templates, review draft reports
- **Business impact**: None yet - this is foundation work

#### **Phase 3-4: Early Value (Weeks 5-11)**
- **You'll see**: Working prototype with your data, draft dashboards
- **You'll do**: Test WIP entry, validate calculations vs manual process
- **Business impact**: Preview of future state, identify issues early

#### **Phase 5: Proof of Concept (Weeks 10-13)**
- **You'll see**: Pilot BU using system for actual month-end close
- **You'll do**: Run parallel processes (old + new), reconcile results
- **Business impact**: Gain confidence in accuracy, refine workflows

#### **Phase 6: Full Value (Weeks 13-16)**
- **You'll see**: All BUs onboarded, old spreadsheets retired
- **You'll do**: Use system as primary forecasting tool
- **Business impact**: **Full time savings and accuracy improvements realized**

---

## **6. Team Roles & Governance**

### **6.1 Steering Committee**

**Purpose**: Strategic oversight, issue escalation, funding decisions

**Members**:
- Finance Leadership (Sponsor)
- BU Controllers (Business Owners)
- IT Leadership (Technology Owner)
- Operations Representative

**Cadence**: Monthly (30 minutes)

**Decisions**:
- Approve scope changes
- Resolve cross-BU conflicts
- Approve budget adjustments
- Sign-off on go-live

---

### **6.2 Core Team**

| Role | Team | What They Do | Time Commitment |
|------|------|--------------|-----------------|
| **Project Lead** | Finance Innovation | Overall coordination, stakeholder management | 50% for 16 weeks |
| **Finance SME** | Finance Team | Define requirements, validate calculations, UAT | 25% for 16 weeks |
| **BU Controllers** | Each BU | Provide input, review reports, pilot testing | 10% for 16 weeks |
| **SAC/Datasphere Lead** | Finance Reporting Team | Build reports, data models, user training | 75% for 16 weeks |
| **Calculation Developer** | Data Science Team | Build forecast engine, testing | 75% for 16 weeks |
| **SAP Technical Lead** | IT SAP Team | Connections, security, infrastructure | 25% for 16 weeks |
| **AI Advisor** | Centralized AI Team | Architecture review, best practices | 10% for 16 weeks |

---

### **6.3 Working Team Cadence**

**Weekly Standup** (30 minutes)
- Progress updates
- Blocker resolution
- Next week priorities
- Attended by: Core team

**Bi-Weekly Steering** (30 minutes)
- Milestone reviews
- Risk escalations
- Decision-making
- Attended by: Steering committee

**Monthly Demo** (1 hour)
- Show progress to broader audience
- Gather feedback
- Adjust priorities
- Attended by: All stakeholders

---

## **7. Change Management & Training**

### **7.1 The Change Journey**

This isn't just a technology implementation - it's a **process transformation**. Success depends on user adoption.

#### **Change Impact by Role**

| Role | What Changes | Impact Level | Support Needed |
|------|--------------|--------------|----------------|
| **BU Controllers** | New dashboards, automated accruals | Medium | Training + 1:1 coaching |
| **Finance Analysts** | WIP entry process, new reports | Medium | Training + quick reference |
| **Operations** | Submit WIP monthly | Low | Simple form + instructions |
| **Accounting** | Automated accrual file | Low | One-time training |
| **Leadership** | New executive dashboards | Low | Executive briefing |

### **7.2 Training Plan**

#### **Phase 1: Awareness (Weeks 1-8)**
- Project kickoff presentations to all BUs
- Monthly newsletter updates
- Demo sessions showing progress
- **Goal**: Everyone knows what's coming and why

#### **Phase 2: Skill Building (Weeks 9-13)**
- Role-based training sessions (2 hours per role)
- Hands-on practice with pilot BU data
- Quick reference guides and videos
- Office hours for Q&A
- **Goal**: Users comfortable with new tools

#### **Phase 3: Support (Weeks 13-16 and beyond)**
- Super users identified per BU (2-3 people)
- Help desk process established
- Weekly office hours for first month
- Monthly refresher sessions
- **Goal**: Sustained adoption and proficiency

### **7.3 Training Materials**

We'll create:
- **User guides** (10-15 pages per role, step-by-step with screenshots)
- **Video tutorials** (5-10 minutes each, task-focused)
- **Quick reference cards** (1-page laminated cards for desk)
- **FAQ document** (continuously updated based on questions)
- **Power user community** (monthly calls to share tips and tricks)

### **7.4 Success Factors**

Research shows these factors drive adoption:

✅ **Executive sponsorship** - Leadership visibly supports and uses the system
✅ **Early wins** - Pilot BU becomes advocate for solution
✅ **Ease of use** - Simpler than old process, not more complex
✅ **Clear value** - Users see personal benefit (less manual work)
✅ **Responsive support** - Questions answered quickly
✅ **Continuous improvement** - User feedback drives enhancements

---

## **8. Success Metrics**

### **8.1 How We'll Measure Success**

#### **Accuracy Metrics** (Primary Focus)

| Metric | Baseline | 3-Month Target | 6-Month Target | Measurement |
|--------|----------|----------------|----------------|-------------|
| **Accrual Accuracy** | 85% (manual) | 95% | 98% | % of accruals within 5% of actual invoice |
| **Forecast Accuracy** | 15-20% variance | <10% variance | <8% variance | Outlook vs actuals at 3-month lag |
| **Reconciliation Errors** | 5-10 per month | <2 per month | 0 per month | ITD mismatches with SAP |

#### **Efficiency Metrics**

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| **Time to Prepare Forecast** | 80 hrs/BU/month | 20 hrs/BU/month | User survey + time tracking |
| **Accrual Calculation Time** | 40-60 hours | 5 hours | Time tracking |
| **Data Freshness** | 2-4 weeks lag | <1 day | System timestamp |
| **Monthly Close Timeline** | Day 5-6 | Day 2-3 | Process tracking |

#### **Adoption Metrics**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **WIP Submission Rate** | Target by deadline | % of wells with WIP entered |
| **User Logins** | 80% monthly active users | SAC analytics |
| **Training Completion** | 100% of key users | Training tracker |
| **User Satisfaction** | 4.0+ / 5.0 | Quarterly survey |

#### **Business Impact Metrics**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Capital Reallocation Speed** | <1 week decision cycle | Time from schedule change to approval |
| **Variance Explanation Time** | <2 hours per BU | Time to prepare variance commentary |
| **Audit Findings** | Zero | Audit results |

#### **Data Quality & Governance Metrics**

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Data Validation Pass Rate** | >99% | % of records passing automated validation |
| **Calculation Reconciliation** | 100% | Total Forecast = ITD + Accrual + Outlook |
| **Lineage Completeness** | 100% | All forecasts traceable to source inputs |
| **Security Compliance** | 100% | Users only access authorized BU data |
| **Automated Testing Pass Rate** | 100% before deployment | CI/CD pipeline test results |

### **8.2 Reporting Cadence**

- **Weekly**: Project team reviews technical progress
- **Monthly**: Steering committee reviews business metrics
- **Quarterly**: Executive scorecard on value realization
- **Post-Implementation** (Month 4): Formal benefits realization review

### **8.3 Value Realization Timeline**

```
Month 1-3: Implementation Phase
├─ Value: Minimal (learning curve)
└─ Focus: Accuracy and user adoption

Month 4: First Full Month Live
├─ Value: 30-40% of target benefits
└─ Focus: Process refinement

Month 5-6: Optimization
├─ Value: 70-80% of target benefits
└─ Focus: Efficiency improvements

Month 7+: Steady State
├─ Value: 100% of target benefits
└─ Focus: Continuous improvement
```

---

## **9. Investment & ROI**

### **9.1 Investment Categories**

**One-Time Costs (Implementation)**
- Internal labor (project team time)
- External consulting (architecture review, if needed)
- Infrastructure setup
- Training development
- Testing and validation
- Change management

**Ongoing Costs (Annual)**
- Cloud infrastructure operating costs
- Support and maintenance
- Cost template updates (quarterly)
- Training refreshers

*Detailed cost estimates to be developed during project planning.*

### **9.2 Expected Benefits**

**Quantifiable Benefits:**
- Significant reduction in manual forecast preparation time
- Improved forecast accuracy
- Faster monthly close cycle
- Reduced rework and errors

**Strategic Benefits:**
- **Risk reduction** - Audit-ready, transparent forecasts
- **Strategic agility** - Faster response to market changes
- **Employee satisfaction** - Finance teams do value-added work, not data entry
- **Stakeholder confidence** - Leadership trusts the numbers
- **Foundation for future** - Platform for expanded CapEx categories and analytics

---

## **10. Risks & Mitigation**

| Risk | Impact | Key Mitigations |
|------|--------|-----------------|
| **User Adoption** - Teams resist new process, continue using spreadsheets | High | Involve users early in design; pilot BU as advocates; make process easier than status quo |
| **Calculation Disputes** - Finance disagrees with methodology or results | High | Monthly validation sessions; side-by-side comparisons; document assumptions; allow overrides |
| **Data Quality** - Schedule files inconsistent across BUs | Medium | Strict file format standards; templates and examples; robust validation with clear errors |
| **Timeline Delays** - Integration or resource constraints | Medium | Built-in contingency buffer; weekly progress tracking; MVP-first prioritization |

### **Risk Management Process**

**Monthly Risk Review**:
- Core team identifies new risks
- Updates likelihood and impact
- Adjusts mitigation strategies
- Escalates high risks to steering committee

**Issue Log**:
- Any problem that arises tracked in shared log
- Owner assigned with due date
- Status updated weekly
- Closed when resolved

---

## **11. Strategic Roadmap**

This initiative is **Phase 1 of a multi-phase CapEx transformation** journey.

### **11.1 The Vision**

Build a **unified, driver-based CapEx forecasting platform** that covers:
- ✅ **Phase 1** - Drilling & Completions (this project)
- **Phase 2** - Facilities, Maintenance, Miscellaneous
- **Phase 3** - Predictive Analytics (ML for cost prediction)
- **Phase 4** - Integrated Planning (scenario planning, board-ready reporting)

### **11.2 Roadmap Overview**

| Phase | Focus | Key Deliverables |
|-------|-------|------------------|
| **Phase 1** | D&C CapEx | Automated accruals + outlook forecasts for drilling & completions |
| **Phase 2** | Expanded CapEx | Add Facility, Maintenance, and Miscellaneous projects |
| **Phase 3** | Predictive Analytics | ML models for drilling time and cost overrun prediction |
| **Phase 4** | Integrated Planning | Scenario planning, SAC integration, executive dashboards |

### **11.3 Phase 2: Expanded CapEx**

**What We'll Add**:
- **Facility Projects** - Infrastructure builds tied to milestone schedules
- **Maintenance Projects** - Sustaining capital based on historical run rates
- **Miscellaneous Projects** - Low-materiality items, ad hoc spending

**Why It Matters**: Covers 100% of capital budget, not just D&C

---

### **11.4 Phase 3: Machine Learning Integration (Future)**

**The Evolution**: Hybrid approach combining drivers + predictive analytics

**ML Use Cases**:

1. **Drilling Time Prediction**
   - Model predicts actual drill days based on basin, depth, formation
   - Refines outlook timing (instead of assuming standard days)
   - **Value**: More accurate completion dates

2. **Cost Overrun Prediction**
   - Model flags wells at high risk of budget overrun
   - Based on complexity, weather, vendor, schedule variance
   - **Value**: Early warning system for budget issues

3. **Production Forecasting**
   - Model predicts well performance (informs revenue side)
   - Enables full project NPV visibility
   - **Value**: Better investment decisions

**How It Works**:
- **Driver-based model** provides transparent baseline
- **ML models** provide refinement and risk scoring
- **Finance can override** ML predictions if needed
- **Continuous learning** - models improve over time

**Partner**: Centralized AI Team (already doing similar work on cash forecasting)

---

### **11.5 Phase 4: Integrated Planning (Future)**

**The End Goal**: Single integrated planning platform for CapEx forecasts

**Components**:
- **SAC Planning Model** integrating CapEx drivers
- **Rolling forecasts** with monthly updates
- **Scenario planning** - sensitivity analysis on key drivers
- **Board-ready reporting** - executive summaries and dashboards
- **Cash flow integration** - link to working capital and cash forecasts

**Why It Matters**:
- Finance leadership has single view of capital forecast
- Finance teams work in one platform, not multiple spreadsheets
- Real-time adjustments for changing business conditions
- Strategic planning tied to operational reality

---

## **12. Next Steps**

### **12.1 Immediate Actions (Next 2 Weeks)**

**For Leadership**:
- [ ] Review and approve this business plan
- [ ] Commit team resources per Section 6.2
- [ ] Identify steering committee members
- [ ] Communicate initiative to broader organization

**For Project Team**:
- [ ] Schedule kickoff meeting with all teams
- [ ] Set up project workspace (SharePoint, Teams, etc.)
- [ ] Begin data discovery - collect sample schedules, cost templates
- [ ] Schedule requirements workshops with Finance SMEs

**For BU Controllers**:
- [ ] Designate primary contact for your BU
- [ ] Gather current forecast spreadsheets for comparison
- [ ] Identify pilot BU volunteer
- [ ] Prepare questions for kickoff meeting

### **12.2 Decision Points**

We need your input on:

1. **Pilot BU Selection** - Which BU should go first?
   - Criteria: Representative complexity, engaged sponsor, data availability

2. **Scope Confirmation** - Are we aligned on D&C only for MVP?
   - Or should we include any Facility projects in Phase 1?

3. **Cost Template Ownership** - Who will own and update standard costs?
   - Finance? Engineering? Joint?

4. **Governance Structure** - Who should chair the steering committee?
   - CFO? Controller? Finance Innovation Director?

### **12.3 Success Factors - What We Need From You**

This project will succeed if we have:

✅ **Executive Sponsorship** - Visible leadership support and messaging
✅ **Dedicated Resources** - Team members with protected time (not "extra" work)
✅ **BU Engagement** - Controllers and operations actively participate
✅ **Timely Decisions** - Steering committee responsive to escalations
✅ **Openness to Change** - Willingness to retire old spreadsheet processes
✅ **Patience with Learning Curve** - New tools take time to master

### **12.4 How to Get Involved**

**Want to learn more?**
- Schedule a 1:1 briefing with project lead
- Attend monthly demo sessions (starting Week 4)
- Join pilot BU working group

**Have questions?**
- Email: [Project Lead Email]
- Teams channel: [Link]
- Office hours: [Schedule]

**Want to provide input?**
- Requirements workshops (Week 1-2)
- Demo feedback sessions (monthly)
- User steering group (monthly)

---

## **Appendix A: Glossary of Terms**

| Term | Business Definition |
|------|---------------------|
| **Accrual** | Cost for work completed this month but not yet invoiced (we owe vendors but haven't been billed yet) |
| **AFE** | Authorization for Expenditure - the approved budget for a capital project |
| **D&C** | Drilling & Completions - the process of drilling and completing wells |
| **Driver-Based** | Forecasting method that ties costs directly to operational activities (e.g., well count, schedules) |
| **Drill Schedule** | Operations plan showing when wells will be drilled (spud dates, completion dates) |
| **Frac Schedule** | Operations plan showing when wells will be hydraulically fractured (completed) |
| **ITD** | Incurred-To-Date - actual costs posted in SAP to date |
| **Outlook** | Forward-looking forecast for future costs not yet incurred |
| **WIP** | Work-in-progress - operations estimate of work completed this month (used to calculate accrual) |
| **WBS** | Work Breakdown Structure - SAP's project identifier (each well or project has a WBS) |

---

## **Appendix B: FAQ**

**Q: Will this replace our current forecasting spreadsheets?**
A: Yes, for D&C forecasting. The goal is to retire manual spreadsheets once the system is validated. You'll still use Excel for exports and analysis, but the core forecast will come from the automated system.

**Q: How much training will I need?**
A: 2-hour role-based training session plus ongoing support. The interface is SAC which many already use. Most users report being comfortable within 1-2 weeks.

**Q: What if I disagree with the forecast?**
A: You can override individual projects with justification. The system provides a starting point, but you remain accountable for your BU's forecast. Overrides are tracked and visible.

**Q: Will this increase my workload during implementation?**
A: Short-term yes (requirements, testing, training), but significant long-term reduction. We estimate 10% of your time for 3 months, then 75% time savings ongoing.

**Q: What happens if the system goes down during month-end?**
A: We'll maintain manual process documentation as backup for the first 6 months. After that, high availability architecture minimizes downtime risk.

**Q: Can I still do scenario planning ("what-if" analysis)?**
A: Yes, in Phase 2 we'll add scenario capabilities. For MVP, you can export data and analyze in Excel as you do today.

**Q: How accurate will the forecasts be?**
A: Accuracy targets will be defined during implementation. Accuracy depends on schedule reliability and WIP estimate quality.

**Q: Who sees my data?**
A: Security follows current SAP model - you see your BU's data, Finance sees consolidated, leadership sees executive summary. No change from today's access model.

---

## **Document Control**

**Version**: 1.0
**Date**: January 9, 2025
**Author**: Amol Gulati
**Reviewers**: [TBD - Finance Leadership, BU Controllers]
**Approval**: [TBD]
**Next Review**: At project kickoff

---

**For Questions or More Information**:
- **Project Lead**: [Name, Email, Phone]
- **Finance Sponsor**: [Name, Email]
- **Project Site**: [SharePoint/Teams Link]

---

**End of Business Plan**
