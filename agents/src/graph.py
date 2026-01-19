"""
BNPL Copilot Graph - Agentic Architecture
"""

import os
import time
import asyncio
from pathlib import Path
from typing import Optional, Any
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from .state import AgentState, Intent, create_state

# The 4 Main Nodes
from .nodes.planner import PlannerNode
from .nodes.executor import ExecutorNode
from .nodes.validator import ValidatorNode
from .nodes.narrator import NarratorNode

# ===== NUMPY CONVERSION HELPER =====
import numpy as np
def convert_numpy(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy(obj.tolist())
    return obj


# Load environment
load_dotenv()

# Data path
DATA_PATH = Path(__file__).parent.parent.parent / "data"


def get_llm() -> Optional[ChatGoogleGenerativeAI]:
    """Initialize Gemini LLM."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("[Warning] GOOGLE_API_KEY not set, using fallback mode")
        return None
    
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.1
    )


class BNPLCopilot:
    """
    Agentic BNPL Analytics Copilot.
    
    Architecture:
    1. Planner (Router/Gemini) -> Decides Intent
    2. Executor (Handlers) -> Fetches Data
    3. Validator (Summarizer) -> Checks Quality & Safety
    4. Narrator (GenAI) -> Explains Insights
    """
    
    def __init__(self):
        self.llm = get_llm()
        
        # Initialize the 4 Nodes
        self.planner = PlannerNode(self.llm)
        self.executor = ExecutorNode(str(DATA_PATH), self.llm)
        self.validator = ValidatorNode()
        self.narrator = NarratorNode(self.llm)
    
    async def process(self, query: str, history: list = []) -> str:
        """Process a user query through the 4-node pipeline."""
        start_time = time.time()
        
        # Create state
        state = create_state(query, history)
        
        # 1. PLAN: Classify intent
        print(f"\n[Copilot] Processing: '{query}'")
        state = await self.planner(state)
        print(f"[Copilot] Intent: {state.intent.value}, Entities: {state.entities}")
        
        # 2. EXECUTE: Fetch data
        state = await self.executor.execute(state)
        
        # Clean data (remove numpy types)
        if state.data:
            state.data = convert_numpy(state.data)

        # 3. VALIDATE: Summarize & Safey Check
        data_summary = self.validator.validate_and_summarize(state.data)
        
        # 4. NARRATE: Generate response
        if state.intent == Intent.CONVERSATION:
            # Chat handler already sets response
            response = state.response
        elif state.error:
            response = self.validator.format_fallback(state, error=state.error)
        else:
            try:
                # Prepare args for narrator
                filters_parts = []
                if state.entities.city: filters_parts.append(f"City: {state.entities.city}")
                if state.entities.category: filters_parts.append(f"Category: {state.entities.category}")
                if state.entities.time_period: filters_parts.append(f"Time Period: {state.entities.time_period}")
                if state.entities.limit: filters_parts.append(f"Limit: {state.entities.limit}")
                if state.entities.status: filters_parts.append(f"Status: {state.entities.status}")
                filters_str = ", ".join(filters_parts) if filters_parts else "None"
                
                explain_needed = "No"
                q_lower = state.user_query.lower()
                if state.intent == Intent.CONVERSATION and any(x in q_lower for x in ["what is", "what does", "meaning of", "explain"]):
                     explain_needed = "Yes"
                
                # Generate
                response = await self.narrator.generate_response(state, data_summary, filters_str, explain_needed)
            except Exception as e:
                print(f"[Copilot] Generation error: {e}")
                response = self.validator.format_fallback(state, error=str(e))
        
        # Extract chart data if available
        chart_data = None
        if state.data and isinstance(state.data, dict):
            chart_data = state.data.get("chart_data")
        
        # Track timing
        elapsed = (time.time() - start_time) * 1000
        print(f"[Copilot] Complete in {elapsed:.0f}ms")
        
        # Store for later access (webapp uses these)
        self._last_chart_data = chart_data
        self._last_data = state.data
        
        return response
    
    async def process_with_chart(self, query: str, history: list = []) -> dict:
        """Process query and return response with chart data."""
        response = await self.process(query, history)
        return {
            "response": response,
            "chart_data": getattr(self, '_last_chart_data', None)
        }


# Global copilot instance
_copilot = None


def get_copilot() -> BNPLCopilot:
    """Get or create the global copilot instance."""
    global _copilot
    if _copilot is None:
        _copilot = BNPLCopilot()
    return _copilot


async def run_query(query: str, history: list = []) -> str:
    """Main entry point for processing a query."""
    copilot = get_copilot()
    return await copilot.process(query, history)


async def run_query_with_chart(query: str, history: list = []) -> dict:
    """Process query and return response with chart data."""
    copilot = get_copilot()
    return await copilot.process_with_chart(query, history)


def run_query_sync(query: str, history: list = []) -> str:
    """Synchronous wrapper for run_query."""
    return asyncio.run(run_query(query, history))


def run_query_with_chart_sync(query: str, history: list = []) -> dict:
    """Synchronous wrapper for run_query_with_chart."""
    return asyncio.run(run_query_with_chart(query, history))
