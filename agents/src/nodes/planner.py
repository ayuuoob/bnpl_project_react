"""
Planner Node - Decides which tools to call and in what order.

Takes the classified intent and entities from the Router,
then creates an execution plan using either:
1. KPI tool (preferred for standard metrics)
2. SQL tool (for drill-downs or custom queries)
"""

from typing import Optional
from langchain_openai import ChatOpenAI

from ..state import AgentState, ExecutionPlan
from ..tools.kpi_tool import KPI_CATALOG


# Mapping of intents to preferred tools and KPIs
INTENT_TOOL_MAP = {
    "growth_analytics": {
        "primary": "kpi",
        "kpis": ["gmv", "approval_rate", "active_users", "repeat_user_rate"],
        "tables": ["kpi_daily", "orders", "users"],
    },
    "funnel": {
        "primary": "sql",  # Funnel requires custom queries
        "kpis": ["checkout_conversion", "approval_rate"],
        "tables": ["checkout_events", "orders"],
    },
    "risk": {
        "primary": "kpi",
        "kpis": ["late_rate", "delinquency_buckets"],
        "tables": ["installments", "user_features_daily", "cohorts_signup_week"],
    },
    "merchant_perf": {
        "primary": "kpi",
        "kpis": ["gmv", "dispute_rate", "approval_rate"],
        "tables": ["merchant_features_daily", "orders", "merchants"],
    },
    "disputes_refunds": {
        "primary": "sql",
        "kpis": ["dispute_rate", "refund_rate"],
        "tables": ["disputes_returns", "orders"],
    },
    "ad_hoc": {
        "primary": "sql",
        "kpis": [],
        "tables": ["*"],  # Requires schema validation
    },
}


class PlannerNode:
    """
    Creates an execution plan based on intent and entities.
    
    Strategy:
    1. If requested KPI exists in catalog → use KPI tool
    2. If drill-down needed → add SQL queries
    3. If custom query → use SQL tool with schema validation
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm
    
    async def __call__(self, state: AgentState) -> AgentState:
        """Create execution plan."""
        state.current_node = "planner"
        
        intent_config = INTENT_TOOL_MAP.get(state.intent, INTENT_TOOL_MAP["ad_hoc"])
        
        # Determine primary tool
        primary_tool = self._select_primary_tool(state, intent_config)
        
        # Build primary query
        primary_query = self._build_primary_query(state, primary_tool, intent_config)
        
        # Plan drill-down queries
        drill_downs = self._plan_drill_downs(state, intent_config)
        
        state.plan = ExecutionPlan(
            primary_tool=primary_tool,
            primary_query=primary_query,
            drill_down_queries=drill_downs,
            fallback_strategy=self._get_fallback(primary_tool),
        )
        
        return state
    
    def _select_primary_tool(self, state: AgentState, config: dict) -> str:
        """Select the best tool for this query."""
        # If specific metrics requested and they're in KPI catalog
        if state.entities.metrics:
            available_kpis = set(KPI_CATALOG.keys())
            requested_kpis = set(state.entities.metrics)
            
            if requested_kpis.issubset(available_kpis):
                return "kpi"
        
        # Use intent's preferred tool
        return config.get("primary", "sql")
    
    def _build_primary_query(self, state: AgentState, tool: str, config: dict) -> str:
        """Build the primary query string."""
        if tool == "kpi":
            return self._build_kpi_query(state)
        else:
            return self._build_sql_query(state, config)
    
    def _build_kpi_query(self, state: AgentState) -> str:
        """Build KPI tool query parameters."""
        # Select first requested metric or default based on intent
        if state.entities.metrics:
            kpi_name = state.entities.metrics[0]
        else:
            intent_kpis = INTENT_TOOL_MAP.get(state.intent, {}).get("kpis", [])
            kpi_name = intent_kpis[0] if intent_kpis else "gmv"
        
        # Build query string
        params = [f"kpi_name={kpi_name}"]
        
        if state.entities.time_window:
            params.append(f"start_date={state.entities.time_window.start_date}")
            params.append(f"end_date={state.entities.time_window.end_date}")
        
        if state.entities.group_by:
            params.append(f"group_by={','.join(state.entities.group_by)}")
        
        return "&".join(params)
    
    def _build_sql_query(self, state: AgentState, config: dict) -> str:
        """Build SQL query for execution."""
        intent = state.intent
        
        # Template queries by intent
        if intent == "funnel":
            return self._build_funnel_sql(state)
        elif intent == "disputes_refunds":
            return self._build_disputes_sql(state)
        elif intent == "risk" and "delinquency" in str(state.entities.metrics):
            return self._build_delinquency_sql(state)
        else:
            return self._build_generic_sql(state, config)
    
    def _build_funnel_sql(self, state: AgentState) -> str:
        """Build funnel analysis SQL."""
        time_filter = self._get_time_filter(state)
        
        return f"""
SELECT 
    event_type,
    COUNT(*) as count,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM checkout_events
WHERE {time_filter}
GROUP BY event_type
ORDER BY 
    CASE event_type 
        WHEN 'checkout_start' THEN 1
        WHEN 'checkout_complete' THEN 2
        WHEN 'order_approved' THEN 3
    END
LIMIT 100
""".strip()
    
    def _build_disputes_sql(self, state: AgentState) -> str:
        """Build disputes analysis SQL."""
        time_filter = self._get_time_filter(state, date_column="o.created_at")
        group_by = state.entities.group_by or ["merchant_id"]
        
        return f"""
SELECT 
    d.{group_by[0] if group_by else 'reason'},
    COUNT(*) as dispute_count,
    SUM(d.amount) as dispute_amount,
    COUNT(*) * 1.0 / (SELECT COUNT(*) FROM orders WHERE {time_filter.replace('o.', '')}) as dispute_rate
FROM disputes_returns d
JOIN orders o ON d.order_id = o.order_id
WHERE {time_filter}
GROUP BY d.{group_by[0] if group_by else 'reason'}
ORDER BY dispute_count DESC
LIMIT 20
""".strip()
    
    def _build_delinquency_sql(self, state: AgentState) -> str:
        """Build delinquency bucket SQL."""
        time_filter = self._get_time_filter(state, date_column="due_date")
        
        return f"""
SELECT 
    CASE 
        WHEN late_days BETWEEN 1 AND 7 THEN '1-7 days'
        WHEN late_days BETWEEN 8 AND 30 THEN '8-30 days'
        WHEN late_days BETWEEN 31 AND 60 THEN '31-60 days'
        WHEN late_days > 60 THEN '60+ days'
    END as bucket,
    COUNT(*) as count,
    SUM(late_days) as total_late_days
FROM installments
WHERE status = 'late' AND {time_filter}
GROUP BY bucket
ORDER BY 
    CASE bucket 
        WHEN '1-7 days' THEN 1
        WHEN '8-30 days' THEN 2
        WHEN '31-60 days' THEN 3
        WHEN '60+ days' THEN 4
    END
""".strip()
    
    def _build_generic_sql(self, state: AgentState, config: dict) -> str:
        """Build a generic SQL query based on entities."""
        tables = config.get("tables", ["orders"])
        primary_table = tables[0] if tables else "orders"
        
        time_filter = self._get_time_filter(state)
        group_by = ", ".join(state.entities.group_by) if state.entities.group_by else None
        limit = state.entities.limit or 100
        
        select_clause = "COUNT(*) as count"
        if state.intent == "growth_analytics":
            select_clause = "SUM(amount) as total_amount, COUNT(*) as count"
        
        sql = f"SELECT {select_clause}"
        if group_by:
            sql = f"SELECT {group_by}, {select_clause}"
        
        sql += f"\nFROM {primary_table}"
        sql += f"\nWHERE {time_filter}"
        
        if group_by:
            sql += f"\nGROUP BY {group_by}"
            sql += f"\nORDER BY count DESC"
        
        sql += f"\nLIMIT {limit}"
        
        return sql.strip()
    
    def _get_time_filter(self, state: AgentState, date_column: str = "created_at") -> str:
        """Build time filter clause."""
        if state.entities.time_window:
            start = state.entities.time_window.start_date
            end = state.entities.time_window.end_date
            return f"{date_column} >= '{start}' AND {date_column} <= '{end}'"
        return f"{date_column} >= DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)"
    
    def _plan_drill_downs(self, state: AgentState, config: dict) -> list:
        """Plan additional drill-down queries."""
        drill_downs = []
        
        # If comparison requested, add period-over-period query
        if state.entities.comparison:
            drill_downs.append("PERIOD_COMPARISON")
        
        # If asking about "why", add breakdown queries
        if any(word in state.user_query.lower() for word in ["why", "driver", "cause", "reason"]):
            drill_downs.append("BREAKDOWN_BY_TOP_DIMENSION")
        
        return drill_downs
    
    def _get_fallback(self, primary_tool: str) -> str:
        """Get fallback strategy if primary fails."""
        if primary_tool == "kpi":
            return "sql"
        return "schema_then_sql"
