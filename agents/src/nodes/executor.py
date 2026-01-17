"""
Executor Node - Calls MCP tools and collects results.

Executes the plan created by the Planner node by:
1. First validating schema (if needed)
2. Calling the primary tool (KPI or SQL)
3. Executing drill-down queries
4. Collecting all results for the Validator
"""

import time
from typing import Optional
from langchain_openai import ChatOpenAI

from ..state import AgentState, ToolCall
from ..tools import SchemaTool, KPITool, SQLTool, RiskTool, TraceTool


class ExecutorNode:
    """
    Executes tool calls defined in the execution plan.
    
    Handles:
    - Schema validation before SQL
    - KPI tool invocations
    - SQL tool invocations with guardrails
    - Risk scoring (if requested)
    - Trace logging
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm
        self.schema_tool = SchemaTool()
        self.kpi_tool = KPITool()
        self.sql_tool = SQLTool()
        self.risk_tool = RiskTool()
        self.trace_tool = TraceTool()
    
    async def __call__(self, state: AgentState) -> AgentState:
        """Execute the plan and collect results."""
        state.current_node = "executor"
        
        if not state.plan:
            state.errors.append("No execution plan available")
            return state
        
        # Log execution start
        await self._log_trace(state, "execution_start")
        
        # Execute primary query
        primary_result = await self._execute_primary(state)
        if primary_result:
            state.tool_calls.append(primary_result)
            if primary_result.result:
                state.raw_results.append({
                    "type": "primary",
                    "tool": state.plan.primary_tool,
                    "result": primary_result.result,
                })
        
        # Execute drill-down queries
        for drill_down in state.plan.drill_down_queries:
            drill_result = await self._execute_drill_down(state, drill_down)
            if drill_result:
                state.tool_calls.append(drill_result)
                if drill_result.result:
                    state.raw_results.append({
                        "type": "drill_down",
                        "query": drill_down,
                        "result": drill_result.result,
                    })
        
        # Log execution complete
        await self._log_trace(state, "execution_complete")
        
        return state
    
    async def _execute_primary(self, state: AgentState) -> Optional[ToolCall]:
        """Execute the primary tool call."""
        plan = state.plan
        start_time = time.time()
        
        try:
            if plan.primary_tool == "kpi":
                result = await self._call_kpi(state)
            elif plan.primary_tool == "sql":
                # Validate schema first
                await self._validate_schema(state)
                result = await self._call_sql(state)
            elif plan.primary_tool == "schema":
                result = await self._call_schema(state)
            elif plan.primary_tool == "risk":
                result = await self._call_risk(state)
            else:
                result = f"Unknown tool: {plan.primary_tool}"
            
            latency = (time.time() - start_time) * 1000
            
            return ToolCall(
                tool_name=plan.primary_tool,
                parameters={"query": plan.primary_query},
                result=result,
                latency_ms=latency,
            )
            
        except Exception as e:
            return ToolCall(
                tool_name=plan.primary_tool,
                parameters={"query": plan.primary_query},
                error=str(e),
            )
    
    async def _call_kpi(self, state: AgentState) -> str:
        """Call the KPI tool."""
        # Parse query parameters
        params = {}
        for param in state.plan.primary_query.split("&"):
            if "=" in param:
                key, value = param.split("=", 1)
                if key == "group_by":
                    params[key] = value.split(",")
                else:
                    params[key] = value
        
        # Call KPI tool
        return await self.kpi_tool._arun(
            kpi_name=params.get("kpi_name", "gmv"),
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
            group_by=params.get("group_by"),
        )
    
    async def _call_sql(self, state: AgentState) -> str:
        """Call the SQL tool."""
        return await self.sql_tool._arun(
            query=state.plan.primary_query,
            limit=state.entities.limit,
        )
    
    async def _call_schema(self, state: AgentState) -> str:
        """Call the Schema tool."""
        return await self.schema_tool._arun()
    
    async def _call_risk(self, state: AgentState) -> str:
        """Call the Risk tool."""
        return await self.risk_tool._arun(
            entity_type="user",
            entity_id=state.entities.user_id or "unknown",
        )
    
    async def _validate_schema(self, state: AgentState) -> None:
        """Validate schema before SQL execution."""
        schema_result = await self.schema_tool._arun()
        
        # Add schema to results for reference
        state.raw_results.append({
            "type": "schema_validation",
            "result": schema_result,
        })
    
    async def _execute_drill_down(self, state: AgentState, drill_down: str) -> Optional[ToolCall]:
        """Execute a drill-down query."""
        start_time = time.time()
        
        try:
            if drill_down == "PERIOD_COMPARISON":
                result = await self._execute_period_comparison(state)
            elif drill_down == "BREAKDOWN_BY_TOP_DIMENSION":
                result = await self._execute_breakdown(state)
            else:
                result = f"Unknown drill-down type: {drill_down}"
            
            latency = (time.time() - start_time) * 1000
            
            return ToolCall(
                tool_name="sql",
                parameters={"drill_down": drill_down},
                result=result,
                latency_ms=latency,
            )
            
        except Exception as e:
            return ToolCall(
                tool_name="sql",
                parameters={"drill_down": drill_down},
                error=str(e),
            )
    
    async def _execute_period_comparison(self, state: AgentState) -> str:
        """Execute period comparison query."""
        # Build comparison SQL
        if state.entities.metrics:
            metric = state.entities.metrics[0]
        else:
            metric = "gmv"
        
        # Call KPI for previous period
        from datetime import datetime, timedelta
        
        if state.entities.time_window:
            end = datetime.strptime(state.entities.time_window.start_date, "%Y-%m-%d")
            start = end - timedelta(days=30)
        else:
            end = datetime.now() - timedelta(days=30)
            start = end - timedelta(days=30)
        
        return await self.kpi_tool._arun(
            kpi_name=metric,
            start_date=start.strftime("%Y-%m-%d"),
            end_date=end.strftime("%Y-%m-%d"),
        )
    
    async def _execute_breakdown(self, state: AgentState) -> str:
        """Execute breakdown by top dimension."""
        # Determine best dimension for breakdown
        if state.intent == "merchant_perf":
            group_by = ["merchant_id"]
        elif state.intent == "risk":
            group_by = ["signup_week"]
        else:
            group_by = ["merchant_id"]
        
        if state.entities.metrics:
            metric = state.entities.metrics[0]
        else:
            metric = "gmv"
        
        return await self.kpi_tool._arun(
            kpi_name=metric,
            start_date=state.entities.time_window.start_date if state.entities.time_window else None,
            end_date=state.entities.time_window.end_date if state.entities.time_window else None,
            group_by=group_by,
        )
    
    async def _log_trace(self, state: AgentState, event_type: str) -> None:
        """Log trace for observability."""
        try:
            from datetime import datetime
            latency = (datetime.now() - state.start_time).total_seconds() * 1000
            
            await self.trace_tool._arun(
                event_type=event_type,
                user_query=state.user_query,
                intent=state.intent,
                tool_calls=[tc.model_dump() for tc in state.tool_calls],
                latency_ms=latency,
            )
        except Exception:
            pass  # Don't fail on trace errors
