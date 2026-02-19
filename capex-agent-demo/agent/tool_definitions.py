"""Claude API tool schemas for the CapEx Close Agent.

These definitions are sent to the Claude API as the `tools` parameter.
9 tools covering the 3-step close workflow + supporting queries.
"""

TOOL_DEFINITIONS = [
    {
        "name": "load_wbs_master",
        "description": (
            "Load the WBS Master List — the single wide table with all financial data "
            "per well, including per-category (drill/comp/fb/hu) budget, ITD, VOW, "
            "ops budget, and working interest percentages. This is the foundation for "
            "all calculations."
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
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "calculate_accruals",
        "description": (
            "Step 1 of the close: Calculate gross and net accruals per well per "
            "cost category. Gross Accrual = VOW - ITD. Net Accrual = Gross * WI%. "
            "Detects Negative Accrual and Large Swing exceptions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Filter by business unit, or 'all'.",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "calculate_net_down",
        "description": (
            "Step 2 of the close: Calculate WI% net-down adjustments. For wells "
            "where the system WI% differs from the actual WI%, computes: "
            "Net-Down Adjustment = Total VOW * (System WI% - Actual WI%)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Filter by business unit, or 'all'.",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "calculate_outlook",
        "description": (
            "Step 3 of the close: Calculate future outlook per well per category. "
            "Future Outlook = Ops Budget - (VOW * WI%). Negative outlook means "
            "the well is over budget."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Filter by business unit, or 'all'.",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_exceptions",
        "description": (
            "Get all exceptions detected across all 3 close steps: Negative Accrual, "
            "Large Swing, WI% Mismatch, and Over Budget. Can filter by severity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Filter by business unit, or 'all'.",
                    "default": "all",
                },
                "severity": {
                    "type": "string",
                    "enum": ["all", "HIGH", "MEDIUM"],
                    "description": "Filter exceptions by severity level.",
                    "default": "all",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_well_detail",
        "description": (
            "Get full waterfall detail for a single well: ITD, VOW, gross/net accrual, "
            "WI% net-down adjustment, and future outlook — all per cost category."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "wbs_element": {
                    "type": "string",
                    "description": "The WBS element ID to look up (e.g., 'WBS-1007').",
                }
            },
            "required": ["wbs_element"],
        },
    },
    {
        "name": "generate_journal_entry",
        "description": (
            "Generate the GL journal entry for the monthly close, combining net "
            "accruals with WI% net-down adjustments. Returns debit/credit accounts "
            "and amounts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Filter by business unit, or 'all'.",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_close_summary",
        "description": (
            "Get the final close summary with all totals (gross accrual, net accrual, "
            "net-down adjustment, future outlook) grouped by business unit."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Filter by business unit, or 'all'.",
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "generate_outlook_load_file",
        "description": (
            "Generate the monthly outlook grid for OneStream. Allocates future "
            "outlook per well per category across future months using schedule-based "
            "allocation (linear by day for drill/comp/fb, lump sum for hookup)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_unit": {
                    "type": "string",
                    "description": "Filter by business unit, or 'all'.",
                    "default": "all",
                },
                "months_forward": {
                    "type": "integer",
                    "description": "Number of months to project forward (1-6).",
                    "minimum": 1,
                    "maximum": 6,
                    "default": 6,
                },
            },
            "required": [],
        },
    },
    {
        "name": "ask_user_question",
        "description": (
            "Ask the user a clarifying question and wait for their response. "
            "Use this when you need human judgment before proceeding — for example, "
            "when WI% mismatches are found and you need confirmation to proceed "
            "with net-down adjustments. The user will see radio buttons with your "
            "options and a Continue button."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The question to ask the user.",
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "2-4 answer choices for the user to pick from.",
                    "minItems": 2,
                    "maxItems": 4,
                },
            },
            "required": ["question", "options"],
        },
    },
]
