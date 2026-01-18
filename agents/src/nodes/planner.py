from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from .router import RouterNode

class PlannerNode(RouterNode):
    """
    Planner Node (The "Brain").
    
    Responsibilities:
    1. Analyze user query.
    2. Classify intent (Risk, KPI, Lookup).
    3. Extract entities (Dates, IDs, Categories).
    4. Plan the execution path.
    
    Inherits from RouterNode to reuse the proven Gemini prompt logic.
    """
    def __init__(self, llm: Optional[ChatGoogleGenerativeAI] = None):
        super().__init__(llm)
