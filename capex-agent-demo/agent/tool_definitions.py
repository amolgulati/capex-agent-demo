"""Claude API tool schemas for the CapEx Gross Accrual Agent.

These definitions are sent to the Claude API as the `tools` parameter.
The `session_state` parameter is NOT included — it's injected by the
orchestrator when dispatching tool calls.
"""

TOOL_DEFINITIONS = [
    {
        "name": "load_wbs_master",
        "description": (
            "Load the WBS Master List (project registry) for a given business unit. "
            "Returns WBS elements with project details, counts, and active status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": (
                        "Business unit to filter by. "
                        "Values: 'Permian Basin', 'DJ Basin', 'Powder River', or 'all'"
                    ),
                }
            },
            "required": ["business_unit"],
        },
    },
    {
        "name": "load_itd",
        "description": (
            "Load Incurred-to-Date (ITD) costs from the SAP extract for specified "
            "WBS elements. Returns matched records, unmatched WBS (missing ITD), "
            "and zero-ITD WBS."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "wbs_elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of WBS element IDs to retrieve ITD costs for.",
                }
            },
            "required": ["wbs_elements"],
        },
    },
    {
        "name": "load_vow",
        "description": (
            "Load Value of Work (VOW) estimates from engineers for specified WBS "
            "elements. Returns matched records and unmatched WBS (missing VOW "
            "submissions)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "wbs_elements": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of WBS element IDs to retrieve VOW estimates for.",
                }
            },
            "required": ["wbs_elements"],
        },
    },
    {
        "name": "calculate_accruals",
        "description": (
            "Calculate gross accruals (VOW - ITD) for all loaded WBS elements. "
            "Detects exceptions: Missing ITD, Negative Accrual, Missing VOW, "
            "Large Swing, Zero ITD. Requires load_wbs_master, load_itd, and "
            "load_vow to have been called first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "missing_itd_handling": {
                    "type": "string",
                    "enum": [
                        "use_vow_as_accrual",
                        "exclude_and_flag",
                        "use_prior_period",
                    ],
                    "description": (
                        "How to handle WBS elements with VOW but no ITD. "
                        "'use_vow_as_accrual': treat missing ITD as $0. "
                        "'exclude_and_flag': exclude from calculation. "
                        "'use_prior_period': use prior period's ITD."
                    ),
                }
            },
            "required": ["missing_itd_handling"],
        },
    },
    {
        "name": "get_exceptions",
        "description": (
            "Retrieve the exception report from the most recent accrual "
            "calculation. Can filter by severity level."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {
                    "type": "string",
                    "enum": ["all", "high", "medium", "low"],
                    "description": "Filter exceptions by severity. 'all' returns everything.",
                }
            },
            "required": ["severity"],
        },
    },
    {
        "name": "get_accrual_detail",
        "description": (
            "Get detailed accrual breakdown for a single WBS element, including "
            "VOW, ITD, gross accrual, prior period comparison, and any exceptions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "wbs_element": {
                    "type": "string",
                    "description": "The WBS element ID to look up (e.g., 'WBS-1027').",
                }
            },
            "required": ["wbs_element"],
        },
    },
    {
        "name": "generate_net_down_entry",
        "description": (
            "Generate the net-down journal entry comparing current gross accruals "
            "to prior period. Returns debit/credit accounts, amounts, and per-WBS "
            "detail."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_summary",
        "description": (
            "Get aggregated accrual summary grouped by a dimension "
            "(project type, business unit, or phase)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "group_by": {
                    "type": "string",
                    "enum": ["project_type", "business_unit", "phase"],
                    "description": "Dimension to group accruals by.",
                }
            },
            "required": ["group_by"],
        },
    },
    {
        "name": "generate_outlook",
        "description": (
            "Project future accruals based on the drill/frac schedule. "
            "Uses Linear by Day allocation for drilling and completions phases. "
            "Reference date is January 2026."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "months_forward": {
                    "type": "integer",
                    "description": "Number of months to project forward (1-6).",
                    "minimum": 1,
                    "maximum": 6,
                }
            },
            "required": ["months_forward"],
        },
    },
]
