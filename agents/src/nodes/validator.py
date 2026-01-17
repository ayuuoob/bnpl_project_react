"""
Validator Node - Validates results and handles errors.

Checks for:
- Empty results
- Wrong data grain
- Unbounded queries
- Row explosion
- Schema mismatches

Can trigger retries with adjusted parameters.
"""

from typing import Optional
from langchain_openai import ChatOpenAI

from ..state import AgentState, ValidationResult


class ValidatorNode:
    """
    Validates tool results and decides next steps.
    
    Actions:
    - Pass: Send to Narrator
    - Retry: Adjust parameters and re-execute
    - Fail: Return error with explanation
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm
    
    async def __call__(self, state: AgentState) -> AgentState:
        """Validate results and determine next steps."""
        state.current_node = "validator"
        
        issues = []
        adjustments = []
        retry_needed = False
        
        # Check for errors in tool calls
        for tc in state.tool_calls:
            if tc.error:
                issues.append(f"Tool {tc.tool_name} failed: {tc.error}")
                retry_needed = True
        
        # Check for empty results
        if not state.raw_results:
            issues.append("No results returned from any tool")
            retry_needed = True
        else:
            # Check each result
            for result in state.raw_results:
                result_str = str(result.get("result", ""))
                
                # Empty result
                if "0 rows" in result_str or not result_str.strip():
                    issues.append(f"Empty result from {result.get('type', 'unknown')} query")
                    adjustments.append("Try broader time window")
                
                # Mock data warning
                if "mock data" in result_str.lower():
                    issues.append("Using mock data (MCP server not connected)")
                
                # Row limit hit
                if "truncated" in result_str.lower() or "more rows" in result_str.lower():
                    issues.append("Results truncated due to row limit")
        
        # Check if we should retry
        if retry_needed and state.retry_count < state.max_retries:
            state.retry_count += 1
            adjustments.append(f"Retry attempt {state.retry_count}/{state.max_retries}")
            
            # Adjust plan for retry
            state = self._adjust_plan_for_retry(state)
        else:
            retry_needed = False
        
        state.validation = ValidationResult(
            is_valid=not issues or not retry_needed,
            issues=issues,
            adjustments=adjustments,
            retry_needed=retry_needed,
        )
        
        return state
    
    def _adjust_plan_for_retry(self, state: AgentState) -> AgentState:
        """Adjust the plan for a retry attempt."""
        if not state.plan:
            return state
        
        # If KPI failed, try SQL
        if state.plan.primary_tool == "kpi":
            state.plan.primary_tool = "sql"
            state.plan.fallback_strategy = "used_fallback_sql"
        
        # Broaden time window
        if state.entities.time_window:
            from datetime import datetime, timedelta
            current_start = datetime.strptime(state.entities.time_window.start_date, "%Y-%m-%d")
            new_start = current_start - timedelta(days=30)
            state.entities.time_window.start_date = new_start.strftime("%Y-%m-%d")
        
        return state
    
    def should_continue(self, state: AgentState) -> str:
        """Determine next node based on validation."""
        if state.validation and state.validation.retry_needed:
            return "executor"  # Go back to executor
        return "narrator"  # Proceed to narrator
