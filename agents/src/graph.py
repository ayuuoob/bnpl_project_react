"""
BNPL Analytics Agent - LangGraph State Machine

This is the main entry point for the agent. It assembles the
graph nodes and provides the interface for processing queries.

Graph Flow:
User Query → Router → Planner → Executor → Validator → Narrator → Response
                                    ↑           │
                                    └───────────┘ (retry if needed)
"""

import os
from typing import Optional, Literal, Union
from langgraph.graph import StateGraph, END

from .state import AgentState
from .nodes import (
    RouterNode,
    PlannerNode,
    ExecutorNode,
    ValidatorNode,
    NarratorNode,
)


def get_llm() -> Optional[Union["ChatGoogleGenerativeAI", "ChatOpenAI"]]:
    """
    Initialize LLM - prioritizes Gemini, falls back to OpenAI.
    Returns None if no API key is configured (agent still works with rule-based logic).
    """
    # Try Gemini first (recommended - has free tier)
    google_key = os.getenv("GOOGLE_API_KEY")
    if google_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",  # Fast and free tier friendly
                google_api_key=google_key,
                temperature=0,
            )
        except ImportError:
            print("Warning: langchain-google-genai not installed. Run: pip install langchain-google-genai")
    
    # Fallback to OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                api_key=openai_key,
            )
        except ImportError:
            print("Warning: langchain-openai not installed. Run: pip install langchain-openai")
    
    # No LLM configured - agent will use rule-based logic only
    print("Note: No LLM API key configured. Agent will use rule-based classification only.")
    return None


def create_agent_graph():
    """
    Create the BNPL Analytics Agent graph.
    
    Returns a compiled LangGraph that can process queries.
    """
    # Initialize LLM (optional - agent works without it)
    llm = get_llm()
    
    # Initialize nodes
    router = RouterNode(llm=llm)
    planner = PlannerNode(llm=llm)
    executor = ExecutorNode(llm=llm)
    validator = ValidatorNode(llm=llm)
    narrator = NarratorNode(llm=llm)
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", router)
    workflow.add_node("planner", planner)
    workflow.add_node("executor", executor)
    workflow.add_node("validator", validator)
    workflow.add_node("narrator", narrator)
    
    # Define edges
    workflow.set_entry_point("router")
    workflow.add_edge("router", "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "validator")
    
    # Conditional edge from validator
    def should_retry(state: AgentState) -> Literal["executor", "narrator"]:
        """Determine if we should retry or proceed to narrator."""
        if state.validation and state.validation.retry_needed:
            if state.retry_count < state.max_retries:
                return "executor"
        return "narrator"
    
    workflow.add_conditional_edges(
        "validator",
        should_retry,
        {
            "executor": "executor",
            "narrator": "narrator",
        }
    )
    
    workflow.add_edge("narrator", END)
    
    # Compile and return
    return workflow.compile()


# Create a singleton instance
_agent_graph = None


def get_agent():
    """Get the singleton agent graph instance."""
    global _agent_graph
    if _agent_graph is None:
        _agent_graph = create_agent_graph()
    return _agent_graph


async def run_query(query: str, session_id: Optional[str] = None) -> str:
    """
    Run a query through the agent.
    
    Args:
        query: Natural language question
        session_id: Optional session identifier for tracing
        
    Returns:
        Structured response string
    """
    agent = get_agent()
    
    # Create initial state
    initial_state = AgentState(
        user_query=query,
        session_id=session_id,
    )
    
    # Run the graph
    final_state = await agent.ainvoke(initial_state)
    
    # Return the response
    if isinstance(final_state, dict):
        return final_state.get("final_response", "No response generated")
    return final_state.final_response or "No response generated"


def run_query_sync(query: str, session_id: Optional[str] = None) -> str:
    """Synchronous version of run_query."""
    import asyncio
    return asyncio.run(run_query(query, session_id))


# Demo function
async def demo():
    """Run demo queries."""
    demo_queries = [
        "What was our GMV last month?",
        "Which merchants have the highest dispute rates?",
        "What is our late payment rate by cohort?",
        "How many active users do we have?",
        "What is the checkout conversion rate?",
    ]
    
    print("=" * 60)
    print("BNPL Analytics Agent - Demo")
    print("=" * 60)
    
    for query in demo_queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print("=" * 60)
        
        response = await run_query(query)
        print(response)
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
