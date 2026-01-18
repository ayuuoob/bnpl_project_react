"""
BNPL Copilot Router - LLM-First Intent Classification

Uses Gemini to classify user intent and extract entities.
"""

import json
import re
from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from ..state import AgentState, Intent, QueryEntities


ROUTER_PROMPT = """You are an intent classifier for a BNPL (Buy Now Pay Later) analytics copilot.

Classify the user's query into ONE of these intents:
- kpi: Business metrics like GMV, approval rate, order count, revenue
- risk: Risk scores, late payments, risky users/installments, explanations
- lookup: User/merchant/order details, lists, filtering by city/category
- comparison: Comparing dimensions (by city, category, time period)
- conversation: Greetings, help, general questions

Also extract any entities mentioned:
- user_id: e.g. "user_00025" or "user 25"  
- installment_id: e.g. "inst_0000141"
- order_id: e.g. "order_000081"
- merchant_id: e.g. "merchant_0010"
- category: fashion, electronics, travel, home
- city: Casablanca, Marrakech, Rabat
- metric: GMV, approval_rate, late_rate, etc.
- limit: number for "top N" queries

User query: {query}

Respond in JSON format ONLY:
{{
    "intent": "kpi|risk|lookup|comparison|conversation",
    "confidence": 0.0-1.0,
    "entities": {{
        "user_id": null or "user_XXXXX",
        "installment_id": null or "inst_XXXXXXX",
        "order_id": null or "order_XXXXXX",
        "merchant_id": null or "merchant_XXXX",
        "category": null or "fashion|electronics|travel|home",
        "city": null or "Casablanca|Marrakech|Rabat",
        "metric": null or "metric name",
        "limit": null or number
    }}
}}"""


class RouterNode:
    """
    LLM-first router using Gemini for intent classification.
    
    Fast, clean, and accurate classification with entity extraction.
    """
    
    def __init__(self, llm: Optional[ChatGoogleGenerativeAI] = None):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(ROUTER_PROMPT)
    
    async def __call__(self, state: AgentState) -> AgentState:
        """Classify intent and extract entities from user query."""
        state.current_node = "router"
        query = state.user_query.strip()
        
        # Handle empty query
        if not query:
            state.intent = Intent.CONVERSATION
            state.confidence = 1.0
            return state
        
        # Quick check for greetings (no LLM needed)
        if self._is_greeting(query):
            state.intent = Intent.CONVERSATION
            state.confidence = 1.0
            return state
        
        # Use LLM for classification
        if self.llm:
            try:
                result = await self._llm_classify(query)
                state.intent = Intent(result["intent"])
                state.confidence = result.get("confidence", 0.8)
                state.entities = self._parse_entities(result.get("entities", {}))
                print(f"[Router] LLM classified: {state.intent.value} (confidence: {state.confidence:.2f})")
            except Exception as e:
                print(f"[Router] LLM error: {e}, using fallback")
                self._fallback_classify(state, query)
        else:
            print("[Router] No LLM, using fallback")
            self._fallback_classify(state, query)
        
        return state
    
    async def _llm_classify(self, query: str) -> dict:
        """Use Gemini to classify intent."""
        chain = self.prompt | self.llm
        response = await chain.ainvoke({"query": query})
        
        # Parse JSON from response
        content = response.content
        
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            content = json_match.group(1)
        
        return json.loads(content)
    
    def _is_greeting(self, query: str) -> bool:
        """Check if query is a simple greeting."""
        greetings = [
            "hello", "hi", "hey", "bonjour", "salut",
            "good morning", "good afternoon", "good evening",
            "how are you", "what's up", "yo"
        ]
        query_lower = query.lower().strip()
        return any(query_lower.startswith(g) or query_lower == g for g in greetings)
    
    def _fallback_classify(self, state: AgentState, query: str):
        """Simple keyword-based fallback classification."""
        query_lower = query.lower()
        
        # Risk keywords
        if any(w in query_lower for w in ["risk", "risky", "late", "why", "explain", "reason"]):
            state.intent = Intent.RISK
            state.confidence = 0.7
        # KPI keywords
        elif any(w in query_lower for w in ["gmv", "revenue", "rate", "total", "kpi", "metric"]):
            state.intent = Intent.KPI
            state.confidence = 0.7
        # Lookup keywords
        elif any(w in query_lower for w in ["show", "list", "user", "merchant", "order"]):
            state.intent = Intent.LOOKUP
            state.confidence = 0.7
        # Comparison keywords
        elif any(w in query_lower for w in ["compare", "by city", "by category", "vs"]):
            state.intent = Intent.COMPARISON
            state.confidence = 0.7
        else:
            state.intent = Intent.CONVERSATION
            state.confidence = 0.5
        
        # Extract entities
        self._extract_entities_fallback(state, query)
    
    def _extract_entities_fallback(self, state: AgentState, query: str):
        """Extract entities using regex patterns."""
        entities = QueryEntities()
        
        # User ID
        match = re.search(r'user[_\s]?(\d+)', query, re.IGNORECASE)
        if match:
            entities.user_id = f"user_{match.group(1).zfill(5)}"
        
        # Installment ID
        match = re.search(r'inst[_\s]?(\d+)', query, re.IGNORECASE)
        if match:
            entities.installment_id = f"inst_{match.group(1).zfill(7)}"
        
        # Order ID
        match = re.search(r'order[_\s]?(\d+)', query, re.IGNORECASE)
        if match:
            entities.order_id = f"order_{match.group(1).zfill(6)}"
        
        # City
        for city in ["casablanca", "marrakech", "rabat"]:
            if city in query.lower():
                entities.city = city.capitalize()
                break
        
        # Category
        for cat in ["fashion", "electronics", "travel", "home"]:
            if cat in query.lower():
                entities.category = cat
                break
        
        # Limit (top N)
        match = re.search(r'top\s*(\d+)', query, re.IGNORECASE)
        if match:
            entities.limit = int(match.group(1))
        
        state.entities = entities
    
    def _parse_entities(self, raw: dict) -> QueryEntities:
        """Parse entities from LLM response."""
        return QueryEntities(
            user_id=raw.get("user_id"),
            installment_id=raw.get("installment_id"),
            order_id=raw.get("order_id"),
            merchant_id=raw.get("merchant_id"),
            category=raw.get("category"),
            city=raw.get("city"),
            metric=raw.get("metric"),
            limit=raw.get("limit")
        )
