"""
LangGraph State Definition for BNPL Analytics Agent.

Defines the state that flows through the graph nodes:
Router → Planner → Executor → Validator → Narrator
"""

from typing import Optional, List, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime


class TimeRange(BaseModel):
    """Time range for queries."""
    start_date: str
    end_date: str


class QueryEntities(BaseModel):
    """Extracted entities from user query."""
    
    metrics: List[str] = Field(default_factory=list, description="KPIs requested")
    time_window: Optional[TimeRange] = None
    merchant_id: Optional[str] = None
    user_id: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    cohort: Optional[str] = None
    group_by: List[str] = Field(default_factory=list, description="Dimensions for breakdown")
    limit: Optional[int] = None
    comparison: bool = Field(default=False, description="Whether to compare periods")


class ToolCall(BaseModel):
    """Record of a tool invocation."""
    
    tool_name: str
    parameters: dict = Field(default_factory=dict)
    result: Optional[str] = None
    error: Optional[str] = None
    latency_ms: Optional[float] = None


class ExecutionPlan(BaseModel):
    """Plan for executing the query."""
    
    primary_tool: Literal["kpi", "sql", "schema", "risk"]
    primary_query: str
    drill_down_queries: List[str] = Field(default_factory=list)
    fallback_strategy: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of validating tool outputs."""
    
    is_valid: bool
    issues: List[str] = Field(default_factory=list)
    adjustments: List[str] = Field(default_factory=list)
    retry_needed: bool = False


class AgentState(BaseModel):
    """
    State that flows through the LangGraph nodes.
    
    Updated by each node as the query is processed.
    """
    
    # Input
    user_query: str
    session_id: Optional[str] = None
    
    # Router output
    intent: Optional[Literal[
        "growth_analytics", 
        "funnel", 
        "risk", 
        "merchant_perf", 
        "disputes_refunds", 
        "ad_hoc"
    ]] = None
    entities: QueryEntities = Field(default_factory=QueryEntities)
    
    # Planner output
    plan: Optional[ExecutionPlan] = None
    
    # Executor output
    tool_calls: List[ToolCall] = Field(default_factory=list)
    raw_results: List[dict] = Field(default_factory=list)
    
    # Validator output
    validation: Optional[ValidationResult] = None
    retry_count: int = 0
    max_retries: int = 1
    
    # Narrator output
    final_response: Optional[str] = None
    
    # Metadata
    start_time: datetime = Field(default_factory=datetime.now)
    current_node: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    
    class Config:
        arbitrary_types_allowed = True


class ResponseFormat(BaseModel):
    """Structured response format."""
    
    summary: str = Field(description="1-3 line answer summary")
    key_metrics: List[dict] = Field(default_factory=list)
    drivers: List[str] = Field(default_factory=list, description="Why bullets")
    recommendations: List[dict] = Field(default_factory=list)
    data_assumptions: dict = Field(default_factory=dict)
