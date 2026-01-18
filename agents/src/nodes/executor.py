from typing import Dict, Any, Optional
from pathlib import Path
from ..state import AgentState, Intent
from ..handlers import KPIHandler, RiskHandler, LookupHandler, ChatHandler
from langchain_google_genai import ChatGoogleGenerativeAI

class ExecutorNode:
    """
    Executor Node (The "Muscle").
    
    Responsibilities:
    1. Initialize specific data handlers (KPI, Risk, Lookup).
    2. Dispatch the query to the correct handler based on Intent.
    3. Return the raw data/state.
    """
    
    def __init__(self, data_path: str, llm: Optional[ChatGoogleGenerativeAI]):
        self.handlers = {
            Intent.KPI: KPIHandler(data_path),
            Intent.RISK: RiskHandler(data_path),
            Intent.LOOKUP: LookupHandler(data_path),
            Intent.COMPARISON: LookupHandler(data_path),  # Reuse lookup for now
            Intent.CONVERSATION: ChatHandler(llm)
        }

    async def execute(self, state: AgentState) -> AgentState:
        """Execute the task based on intent."""
        handler = self.handlers.get(state.intent)
        if not handler:
            print(f"[Executor] No handler found for intent: {state.intent}")
            return state
            
        return await handler.handle(state)
