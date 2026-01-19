"""
BNPL Copilot State - Simplified Version

Defines the state that flows through the agent graph.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class Intent(str, Enum):
    """Simplified intent classification."""
    KPI = "kpi"                    # Business metrics (GMV, approval rate, etc.)
    RISK = "risk"                  # Risk analysis (scores, explanations)
    LOOKUP = "lookup"              # Data lookups (users, merchants, orders)
    COMPARISON = "comparison"      # Compare dimensions
    CONVERSATION = "conversation"  # Greetings, help, general chat


class QueryEntities(BaseModel):
    """Entities extracted from user query."""
    user_id: Optional[str] = None
    installment_id: Optional[str] = None
    order_id: Optional[str] = None
    merchant_id: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None
    time_period: Optional[str] = None  # e.g. "last 30 days", "this month"
    limit: Optional[int] = None        # e.g. "top 5"
    metric: Optional[str] = None       # e.g. "GMV", "approval rate"


class AgentState(BaseModel):
    """
    Simplified agent state for BNPL Copilot.
    
    Flow: Query → Router → Handler → Response
    """
    
    # Input
    user_query: str = ""
    
    # Classification (from Router)
    intent: Intent = Intent.CONVERSATION
    entities: QueryEntities = Field(default_factory=QueryEntities)
    confidence: float = 0.0
    
    # Execution (from Handler)
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Output (from Response Generator)
    response: str = ""
    chart_data: Optional[Dict[str, Any]] = None
    
    # Context
    history: List[Dict[str, str]] = []  # List of {"role": "user"|"assistant", "content": "..."}
    
    # Metadata
    current_node: str = ""
    processing_time_ms: float = 0.0


# Quick helpers
def create_state(query: str, history: List[Dict[str, str]] = []) -> AgentState:
    """Create a new agent state from a user query."""
    return AgentState(user_query=query, history=history)


def is_risk_query(state: AgentState) -> bool:
    """Check if this is a risk-related query."""
    return state.intent == Intent.RISK


def is_lookup_query(state: AgentState) -> bool:
    """Check if this is a data lookup query."""
    return state.intent == Intent.LOOKUP


def has_entity(state: AgentState, entity_type: str) -> bool:
    """Check if a specific entity was extracted."""
    return getattr(state.entities, entity_type, None) is not None
