# CapEx Accrual Agent — Town Hall Demo App Spec

**Purpose:** Build a Streamlit web app that demonstrates an AI agent calculating CapEx gross accruals using synthetic data. The agent shows its reasoning, calls tools, asks clarifying questions, and produces outputs — making the concept of "agentic AI" tangible for a Finance audience that has never seen one work.

**Audience:** Finance department town hall (~100+ people, mostly non-technical)
**Hosting:** Streamlit Cloud (free), Hugging Face Spaces, or similar
**LLM:** Claude API (Sonnet for cost efficiency, or Haiku for speed)
**Data:** 100% synthetic — no real Oxy data

> This document contains all domain context needed to build the demo in a fresh repo. No access to the finance-ai-program repo is needed during development.

---

## 1. What the Demo Should Do

### The User Experience (Town Hall Flow)

You open the app in a browser. It has a clean chat interface with a sidebar showing "Agent Status" and "Tools Available."

**Step 1 — You type a prompt:**
> "Calculate the CapEx gross accrual for Permian Basin, January 2026"

**Step 2 — The agent shows its thinking (streaming, visible breadcrumbs):**
```
Thinking: I need to calculate gross accruals. This requires three data sources:
  1. WBS Master List (project registry)
  2. ITD costs (Incurred-to-Date from SAP)
  3. WIP/VOW estimates (Work-in-Progress from engineers)

Step 1: Loading WBS Master List...
  > Found 47 active WBS elements for Permian Basin

Step 2: Loading ITD extract from SAP...
  > Matched 44 of 47 WBS elements to ITD records
  > 3 WBS elements have no ITD match (flagging as exceptions)

Step 3: Loading WIP/VOW estimates from engineers...
  > Matched 42 of 47 WBS elements to WIP submissions
  > 2 additional WBS elements missing WIP data
```

**Step 3 — The agent asks a clarifying question (interactive UI element):**
```
I found 3 WBS elements with WIP estimates but no ITD costs in SAP.
How should I handle these?

  [ ] Use WIP as full accrual (assume zero ITD)        ← selectable
  [ ] Exclude from calculation and flag for review      ← selectable
  [ ] Use last month's ITD as estimate                  ← selectable
```

You select an option (space + enter style, or radio buttons in Streamlit).

**Step 4 — The agent calculates and shows its work:**
```
Step 4: Calculating gross accruals...
  > Gross Accrual = WIP/VOW − ITD for each WBS element
  > Processing 47 WBS elements...

Step 5: Running exception checks...
  > Found 7 exceptions across 5 categories:
    - 3x Missing ITD (High severity)
    - 1x Negative Accrual (High severity) — WBS-2847: ITD exceeds WIP by $127K
    - 1x Large Swing >25% (Medium severity) — WBS-1923: +34% vs prior period
    - 2x Missing WIP (Medium severity)

Step 6: Generating outputs...
```

**Step 5 — The agent displays results:**

A formatted summary table, exception report, and optional net-down/outlook view. Downloadable as Excel.

```
═══════════════════════════════════════════════════════
  PERMIAN BASIN — JANUARY 2026 GROSS ACCRUAL SUMMARY
═══════════════════════════════════════════════════════

  Total WBS Elements:        47
  Successfully Calculated:   42
  Exceptions Flagged:         7
  ─────────────────────────────────
  Total Gross Accrual:    $14.3M
  Prior Period:           $12.8M
  Change:                 +$1.5M (+11.7%)
═══════════════════════════════════════════════════════
```

**Step 6 — You can ask follow-up questions:**
> "Which wells have the largest accruals?"
> "Show me all negative accruals"
> "What would the outlook look like if we apply the Q1 drill schedule?"

---

## 2. Domain Context (For the LLM System Prompt)

### What is a CapEx Gross Accrual?

In oil & gas accounting, capital expenditures (CapEx) are tracked at the **WBS Element** level (Work Breakdown Structure — essentially a project/well identifier).

Each month, Finance needs to calculate how much cost has been **incurred but not yet recorded in SAP**. This is the **gross accrual**.

**The math is a subtraction:**
```
Gross Accrual = WIP/VOW (engineer estimate of work done) − ITD (costs already in SAP)
```

- **WIP/VOW (Work-in-Progress / Value of Work):** What the engineers say has been done. Comes from BU engineers as Excel files.
- **ITD (Incurred-to-Date):** What SAP says has been invoiced/recorded. Comes from SAP ERP extract.
- **WBS Element:** The project identifier that ties everything together (like a well or facility project).

**Example:**
- Engineers say $5M of work is done on Well ABC (WIP = $5M)
- SAP shows $3.2M has been invoiced (ITD = $3.2M)
- Gross Accrual = $5M − $3.2M = **$1.8M** (this amount needs to be booked)

### What is the Net-Down Entry?

After calculating the gross accrual, Finance creates a **net-down journal entry** that adjusts the books:
```
Net-Down = Current Period Gross Accrual − Prior Period Gross Accrual
```

This is the actual journal entry amount. If last month's accrual was $1.5M and this month's is $1.8M, the net-down entry is **$300K** (the incremental change).

### What is the Outlook?

The **outlook** projects future accruals based on the drill/frac schedule and cost templates:
- How many wells are planned for the next 3-6 months?
- What are the expected costs per well phase (drill, complete, equip)?
- When will those costs hit SAP vs. when will work be done?

### Exception Types

| Exception | Condition | Severity | What It Means |
|-----------|-----------|----------|---------------|
| **Missing ITD** | WBS has WIP but no SAP costs | High | Work done but nothing invoiced — needs investigation |
| **Negative Accrual** | ITD exceeds WIP (accrual < 0) | High | More invoiced than work done — possible overbilling or WIP underestimate |
| **Missing WIP** | WBS in master list but no WIP from engineers | Medium | Engineers didn't submit — chase for input |
| **Large Swing** | Accrual differs >25% from prior period | Medium | Big change — needs explanation (could be legitimate) |
| **Zero ITD** | WBS has WIP but zero in SAP | Low | New project — work started but no invoices yet |

### Why This Matters to the Audience

- **BU Controllers** do this calculation manually every month. It takes 40-60 hours.
- **FP&A** consumes these numbers for the capital forecast.
- **Leadership** sees the consolidated number and needs it to be right.
- **Auditors** need a trail from WIP/ITD inputs to the accrual output.

An agent that automates this, shows its work, and catches exceptions is immediately understood as valuable by anyone in the room.

---

## 3. Synthetic Data Design

### File 1: `wbs_master.csv` — WBS Master List

Generate ~50 rows. These are the "projects" (wells).

| Column | Type | Example Values |
|--------|------|----------------|
| `wbs_element` | String | "WBS-1001", "WBS-1002", ... |
| `well_name` | String | "Permian Eagle 14H", "Delaware Basin 7-2H", ... |
| `project_type` | String | "Drilling", "Completion", "Facilities", "Workover" |
| `business_unit` | String | "Permian Basin", "DJ Basin", "Powder River" |
| `afe_number` | String | "AFE-2026-0014", ... |
| `status` | String | "Active", "Complete", "Suspended" |
| `budget_amount` | Float | $2M - $15M range |
| `start_date` | Date | Various 2025-2026 dates |

### File 2: `itd_extract.csv` — Incurred-to-Date (SAP)

Match ~44 of the 50 WBS elements (leave some unmatched to create exceptions).

| Column | Type | Example Values |
|--------|------|----------------|
| `wbs_element` | String | Matches wbs_master |
| `itd_amount` | Float | $0 - $12M range |
| `last_posting_date` | Date | Recent dates |
| `cost_category` | String | "Material", "Service", "Labor", "Equipment" |
| `vendor_count` | Int | 1-15 |

### File 3: `wip_vow.csv` — WIP/VOW Estimates (Engineers)

Match ~45 of the 50 WBS elements (different gaps than ITD to create different exception types).

| Column | Type | Example Values |
|--------|------|----------------|
| `wbs_element` | String | Matches wbs_master |
| `wip_amount` | Float | Generally higher than ITD (most accruals are positive) |
| `submission_date` | Date | "2026-01-28" (recent) |
| `engineer_name` | String | Synthetic names |
| `phase` | String | "Drilling", "Completion", "Flowback", "Equip" |
| `pct_complete` | Float | 0-100% |

### File 4: `prior_period_accruals.csv` — Last Month's Accruals

For large-swing detection.

| Column | Type |
|--------|------|
| `wbs_element` | String |
| `prior_gross_accrual` | Float |
| `period` | String ("2025-12") |

### File 5: `drill_schedule.csv` — Forward-Looking Schedule (for Outlook)

| Column | Type | Example Values |
|--------|------|----------------|
| `wbs_element` | String | |
| `planned_phase` | String | "Spud", "TD", "Frac Start", "Frac End", "First Production" |
| `planned_date` | Date | Q1-Q2 2026 dates |
| `estimated_cost` | Float | Per-phase cost estimate |

### Data Design Rules

1. **Make ~80% of records clean** — accruals calculate normally
2. **Create 3 Missing ITD exceptions** — WBS in WIP but not in ITD
3. **Create 1 Negative Accrual** — ITD > WIP (overbilling scenario)
4. **Create 1 Large Swing** — >25% change from prior period
5. **Create 2 Missing WIP exceptions** — WBS in master but no WIP submitted
6. **Make dollar amounts realistic** — oil & gas wells cost $3M-$15M for D&C
7. **Use realistic well names** — "Permian Eagle 14H", "Wolfcamp A 22-1H", etc.

---

## 4. Technical Architecture

### Stack

| Component | Tool | Notes |
|-----------|------|-------|
| **Frontend** | Streamlit | Chat interface with `st.chat_message`, `st.status` for breadcrumbs |
| **LLM** | Claude API (Anthropic SDK) | Sonnet for reasoning quality, Haiku for speed/cost |
| **Data** | Pandas + CSV files | Loaded at startup, queried by agent tools |
| **Hosting** | Streamlit Cloud or HF Spaces | Free tier, public URL |
| **Streaming** | Anthropic streaming API | Shows thinking in real-time |

### Project Structure

```
capex-agent-demo/
├── app.py                    # Streamlit app (main entry point)
├── agent/
│   ├── __init__.py
│   ├── orchestrator.py       # Agent loop: prompt → think → tool call → respond
│   ├── tools.py              # Python functions the agent can call
│   ├── prompts.py            # System prompt with domain context
│   └── clarifications.py    # Clarifying question logic
├── data/
│   ├── wbs_master.csv
│   ├── itd_extract.csv
│   ├── wip_vow.csv
│   ├── prior_period_accruals.csv
│   └── drill_schedule.csv
├── utils/
│   ├── formatting.py         # Output formatting (tables, summaries)
│   └── excel_export.py       # Generate downloadable Excel
├── requirements.txt          # streamlit, anthropic, pandas, openpyxl
├── .streamlit/
│   └── config.toml           # Theme settings
└── README.md
```

### Agent Orchestration Pattern

The agent uses Claude's **tool use** capability. The flow:

```
1. User sends message
2. System prompt provides domain context + available tools
3. Claude decides which tool to call (or asks a question)
4. App executes the tool, returns result to Claude
5. Claude reasons about the result, decides next step
6. Repeat until Claude has enough info to respond
7. Final response rendered with formatted output
```

### Registered Tools (for Claude tool_use)

```python
tools = [
    {
        "name": "load_wbs_master",
        "description": "Load the WBS Master List for a given business unit. Returns project/well details including WBS element, well name, project type, AFE number, status, and budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Business unit to filter by (e.g., 'Permian Basin', 'DJ Basin', or 'all')"
                }
            },
            "required": ["business_unit"]
        }
    },
    {
        "name": "load_itd",
        "description": "Load Incurred-to-Date (ITD) costs from SAP for the specified WBS elements. ITD represents costs already invoiced and recorded in the ERP system.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wbs_elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of WBS element IDs to retrieve ITD for"
                }
            },
            "required": ["wbs_elements"]
        }
    },
    {
        "name": "load_wip",
        "description": "Load Work-in-Progress / Value of Work (WIP/VOW) estimates submitted by BU engineers for the specified WBS elements. WIP represents the engineer's estimate of work completed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wbs_elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of WBS element IDs to retrieve WIP for"
                }
            },
            "required": ["wbs_elements"]
        }
    },
    {
        "name": "calculate_accruals",
        "description": "Calculate gross accruals (WIP minus ITD) for each WBS element. Returns accrual amount per WBS and flags exceptions (missing data, negative accruals, large swings).",
        "input_schema": {
            "type": "object",
            "properties": {
                "missing_itd_handling": {
                    "type": "string",
                    "enum": ["use_wip_as_accrual", "exclude_and_flag", "use_prior_period"],
                    "description": "How to handle WBS elements with WIP but no ITD"
                }
            },
            "required": ["missing_itd_handling"]
        }
    },
    {
        "name": "get_exceptions",
        "description": "Retrieve exception report showing all flagged items by severity (High, Medium, Low). Includes exception type, WBS element, details, and recommended action.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["all", "high", "medium", "low"],
                    "description": "Filter by severity level"
                }
            },
            "required": ["severity"]
        }
    },
    {
        "name": "get_accrual_detail",
        "description": "Get detailed accrual breakdown for a specific WBS element, including ITD, WIP, accrual amount, prior period comparison, and any exceptions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "wbs_element": {
                    "type": "string",
                    "description": "The WBS element ID to look up"
                }
            },
            "required": ["wbs_element"]
        }
    },
    {
        "name": "generate_net_down_entry",
        "description": "Generate the net-down journal entry by comparing current gross accruals to prior period. Net-Down = Current Gross Accrual minus Prior Period Gross Accrual. Returns the journal entry amount and GL account mapping.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "generate_outlook",
        "description": "Project future accruals based on the drill/frac schedule and cost templates. Shows expected accrual trajectory for the next 3-6 months.",
        "input_schema": {
            "type": "object",
            "properties": {
                "months_forward": {
                    "type": "integer",
                    "description": "Number of months to project forward (1-6)"
                }
            },
            "required": ["months_forward"]
        }
    },
    {
        "name": "get_summary",
        "description": "Get aggregated accrual summary grouped by a dimension (project type, business unit, or phase).",
        "input_schema": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "enum": ["project_type", "business_unit", "phase"],
                    "description": "Dimension to group accruals by"
                }
            },
            "required": ["group_by"]
        }
    }
]
```

---

## 5. System Prompt (for Claude)

```
You are a CapEx Gross Accrual Agent — an AI assistant that helps Finance teams
calculate, analyze, and review capital expenditure accruals.

## Your Role
You automate Step 1 of the CapEx forecasting process: calculating gross accruals
by matching Work-in-Progress (WIP/VOW) estimates from engineers against
Incurred-to-Date (ITD) costs from SAP.

## The Core Calculation
Gross Accrual = WIP/VOW (engineer estimate of work done) − ITD (costs in SAP)

## How You Work
1. You have access to tools that load data from the WBS Master List, ITD extract,
   and WIP/VOW files.
2. You ALWAYS show your reasoning step by step.
3. You flag exceptions and explain why they matter.
4. When you encounter ambiguous situations (like missing data), you ASK the user
   how to proceed rather than making assumptions.
5. You can generate net-down journal entries and forward-looking outlooks.

## Exception Rules
- Missing ITD (WBS has WIP but no SAP costs): HIGH severity
- Negative Accrual (ITD > WIP): HIGH severity
- Missing WIP (WBS in master but no engineer submission): MEDIUM severity
- Large Swing (>25% change from prior period): MEDIUM severity
- Zero ITD (WBS has WIP but zero SAP costs): LOW severity

## Communication Style
- Use Finance/Accounting terminology naturally
- Show your work — every number should be traceable
- Be concise but thorough
- When presenting results, use formatted tables
- Always mention the total count, total dollar amount, and any exceptions

## Important
- This is a DEMO with SYNTHETIC DATA. All numbers, well names, and WBS elements
  are fictional.
- You are demonstrating the concept of an agentic workflow — tool calling,
  reasoning, exception handling, and interactive decision-making.
```

---

## 6. UI Design (Streamlit)

### Layout

```
┌─────────────────────────────────────────────────────────────┐
│  HEADER: "CapEx Gross Accrual Agent"                         │
│  Subtitle: "Finance AI Demo — Synthetic Data"                │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│  SIDEBAR         │  MAIN CHAT AREA                          │
│                  │                                          │
│  Agent Status    │  [Chat messages with streaming]           │
│  ● Ready         │                                          │
│                  │  USER: "Calculate the gross accrual      │
│  Tools Available │   for Permian Basin, Jan 2026"           │
│  ☑ load_wbs      │                                          │
│  ☑ load_itd      │  AGENT: [thinking breadcrumbs]           │
│  ☑ load_wip      │         [tool calls with results]        │
│  ☑ calc_accruals │         [clarifying question]            │
│  ☑ exceptions    │         [final output]                   │
│  ☑ net_down      │                                          │
│  ☑ outlook       │  ┌──────────────────────────────────┐    │
│  ☑ summary       │  │  📊 Accrual Summary Table         │    │
│                  │  │  ⚠️ Exception Report               │    │
│  Data Loaded     │  │  📥 Download Excel                 │    │
│  47 WBS elements │  └──────────────────────────────────┘    │
│  44 ITD records  │                                          │
│  45 WIP records  │  ┌──────────────────────────────────┐    │
│                  │  │  💬 Type your message...     [Send]│    │
│  [Reset Demo]    │  └──────────────────────────────────┘    │
│                  │                                          │
└──────────────────┴──────────────────────────────────────────┘
```

### Key UI Components

**1. Streaming Breadcrumbs (st.status)**
```python
with st.status("Agent is thinking...", expanded=True) as status:
    st.write("Loading WBS Master List...")
    # ... tool execution ...
    st.write("Found 47 active WBS elements for Permian Basin")
    st.write("Loading ITD extract from SAP...")
    # ... etc
    status.update(label="Calculation complete!", state="complete")
```

**2. Clarifying Questions (st.radio or st.pills)**
```python
st.write("I found 3 WBS elements with WIP but no ITD. How should I handle these?")
choice = st.radio(
    "Select an option:",
    [
        "Use WIP as full accrual (assume zero ITD)",
        "Exclude from calculation and flag for review",
        "Use last month's ITD as estimate"
    ]
)
if st.button("Continue"):
    # proceed with selected option
```

**3. Results Display (st.dataframe + st.metric)**
```python
col1, col2, col3 = st.columns(3)
col1.metric("Total Gross Accrual", "$14.3M", "+$1.5M")
col2.metric("WBS Elements", "47", "42 calculated")
col3.metric("Exceptions", "7", "2 high severity")

st.dataframe(accrual_summary_df, use_container_width=True)
```

**4. Excel Download**
```python
st.download_button(
    "📥 Download Accrual Schedule (Excel)",
    data=excel_bytes,
    file_name="permian_basin_accruals_jan_2026.xlsx"
)
```

---

## 7. Suggested Demo Script (What to Say at the Town Hall)

**Setup (30 seconds):**
> "I want to show you what an AI agent looks like in action. This is a prototype I built using synthetic data — no real Oxy numbers. It demonstrates what the CapEx Gross Accrual Agent will do when we build it on Databricks later this year."

**Run the demo (2-3 minutes):**
> Type: "Calculate the gross accrual for Permian Basin, January 2026"

> [As the agent thinks] "Watch what's happening — the agent is reading data, matching WBS elements, and showing its work. It's not a black box. You can see every step."

> [When clarifying question appears] "Here's the key part — the agent found a data issue and it's asking me how to handle it instead of guessing. This is what makes it an agent, not just a calculator."

> [Select option, watch it calculate]

> [When results appear] "In production, this replaces 40-60 hours of manual work per month. And every number is traceable."

**Follow-up query (30 seconds):**
> Type: "Show me all negative accruals"
> "I can have a conversation with it. It remembers context."

**Close (15 seconds):**
> "This is Agent #1. Once the pattern is proven, the same architecture works for depreciation checks, forecast variance, journal entry review — anything with rules and data."

---

## 8. Build Sequence

| Step | What | Time Estimate |
|------|------|---------------|
| 1 | Set up fresh repo, install dependencies | 15 min |
| 2 | Generate synthetic CSV data files | 30 min |
| 3 | Build tool functions (load, calculate, exceptions) | 1-2 hrs |
| 4 | Write system prompt and tool definitions | 30 min |
| 5 | Build agent orchestrator (Claude API + tool use loop) | 1-2 hrs |
| 6 | Build Streamlit UI (chat, breadcrumbs, clarifying Qs) | 1-2 hrs |
| 7 | Add net-down entry and outlook tools | 1 hr |
| 8 | Add Excel export | 30 min |
| 9 | Polish UI (sidebar, metrics, theming) | 30 min |
| 10 | Deploy to Streamlit Cloud or HF Spaces | 15 min |
| 11 | Record backup video of the demo | 15 min |
| **Total** | | **~6-9 hours focused work** |

---

## 9. Environment & Dependencies

### requirements.txt
```
streamlit>=1.30.0
anthropic>=0.18.0
pandas>=2.0.0
openpyxl>=3.1.0
```

### .streamlit/config.toml (Dark theme to look professional)
```toml
[theme]
base = "dark"
primaryColor = "#4CAF50"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#1E2329"
textColor = "#FAFAFA"
```

### Environment Variables
```
ANTHROPIC_API_KEY=sk-ant-...  # Set in Streamlit Cloud secrets or .env
```

---

## 10. Hosting Options

| Option | Cost | Setup | URL |
|--------|------|-------|-----|
| **Streamlit Cloud** | Free (public apps) | Connect GitHub repo, auto-deploys | `yourapp.streamlit.app` |
| **Hugging Face Spaces** | Free (basic) | Push to HF repo, select Streamlit SDK | `huggingface.co/spaces/you/app` |
| **Railway** | Free tier available | Docker or Python deploy | Custom domain possible |
| **Render** | Free tier (spins down) | Auto-deploy from GitHub | Custom domain possible |

**Recommendation:** Streamlit Cloud — zero config, auto-deploys from GitHub, free.

---

## 11. Risk Mitigations for the Town Hall

| Risk | Mitigation |
|------|------------|
| **WiFi fails** | Pre-record a 2-minute video of the demo. Play that instead. |
| **API rate limit / outage** | Have a cached response ready. The app can fall back to pre-computed results. |
| **Audience asks "is this real data?"** | Banner on every screen: "DEMO — Synthetic Data." Say it verbally at the start. |
| **Someone asks "when can I use this?"** | "This is Agent #1 on our 2026 roadmap. We're building it on Databricks this year." |
| **Demo takes too long** | Practice the exact prompts. Time it. Cut to 2 minutes max. |

---

## 12. Source Context (From finance-ai-program Repo)

This spec was built from the following source documents. These do NOT need to be in the demo repo — the context is already captured above.

| Document | What Was Used |
|----------|---------------|
| `projects/capex-accrual-agent-charter.md` | Agent logic, inputs/outputs, exception types, build sequence, architecture diagram, tool definitions |
| `projects/capex-forecast.md` | Domain context (ITD/WIP/accrual framework), business value ($40-60 hrs/month savings), phases |
| `planning/finance-ai-agent-architecture-consolidated.md` | Architecture patterns, skill definition standard, orchestration approach, tool registration pattern |
| `playbooks/ai-agent-poc-workshop-strategy.md` | Fixed assets agent workflow example, depreciation check example, month-end close agent pattern |
| `planning/town-hall-deck-outline.md` | Presentation flow context — where this demo fits in the 25-min section |
| `meeting-prep/2026-02-17-melanie-program-review.md` | Strategic context — why this matters to leadership |
| `context/operating-principles.md` | Program principles (explainability, adoption, ownership) |
| `governance/ai-value-adoption-tracker.md` | Value tracking framework the demo supports |

---

*Last updated: February 17, 2026*
