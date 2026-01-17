"""
Router Node - Classifies user intent and extracts entities.

This is the first node in the graph. It analyzes the user's
natural language query to determine:
1. Intent category (growth, funnel, risk, merchant, finance)
2. Entities (metrics, time window, filters, groupings)
"""

import re
from datetime import datetime, timedelta
from typing import Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..state import AgentState, QueryEntities, TimeRange


# Intent patterns for rule-based classification
INTENT_PATTERNS = {
    "growth_analytics": [
        r"\bgmv\b", r"\brevenue\b", r"\bactive users?\b", r"\bgrowth\b",
        r"\bacquisition\b", r"\brepeat\s*(user|rate)\b", r"\bnew users?\b",
        r"\bmonth\s*over\s*month\b", r"\bweek\s*over\s*week\b",
    ],
    "funnel": [
        r"\bconversion\b", r"\bcheckout\b", r"\bapproval\s*rate\b",
        r"\bdrop\s*off\b", r"\babandon\b", r"\bfunnel\b",
    ],
    "risk": [
        r"\blate\b", r"\bdelinquen\w*\b", r"\boverdue\b", r"\brisk\s*score\b",
        r"\bon[\-\s]?time\b", r"\bcohort\s*performance\b", r"\bbucket\b",
    ],
    "merchant_perf": [
        r"\bmerchant\b", r"\btop\s*merchant\b", r"\bmerchant\s*gmv\b",
        r"\bhigh[\-\s]?risk\s*merchant\b", r"\bmerchant\s*performance\b",
    ],
    "disputes_refunds": [
        r"\bdispute\b", r"\brefund\b", r"\bchargeback\b", r"\breturn\b",
    ],
}

# Metric extraction patterns
METRIC_PATTERNS = {
    "gmv": [r"\bgmv\b", r"\bgross\s*merchandise\b", r"\btotal\s*value\b"],
    "approval_rate": [r"\bapproval\s*rate\b", r"\bapproved\s*%\b"],
    "active_users": [r"\bactive\s*users?\b", r"\bmau\b", r"\bdau\b"],
    "repeat_user_rate": [r"\brepeat\s*(user|rate)\b", r"\bretention\b"],
    "late_rate": [r"\blate\s*(payment)?\s*rate\b", r"\boverdue\s*rate\b"],
    "delinquency_buckets": [r"\bdelinquency\s*bucket\b", r"\bbucket\b"],
    "dispute_rate": [r"\bdispute\s*rate\b"],
    "refund_rate": [r"\brefund\s*rate\b"],
    "checkout_conversion": [r"\bcheckout\s*conversion\b", r"\bconversion\s*rate\b"],
    "repayment_velocity": [r"\brepayment\s*velocity\b", r"\bpayment\s*speed\b"],
}


class RouterNode:
    """
    Classifies user intent and extracts query entities.
    
    Uses a hybrid approach:
    1. Rule-based pattern matching for speed
    2. LLM fallback for ambiguous queries
    """
    
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm
        self._router_prompt = self._build_router_prompt()
    
    def _build_router_prompt(self) -> ChatPromptTemplate:
        """Build the LLM router prompt."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an intent classifier for a BNPL analytics agent.

Given a user query, extract:
1. intent: One of [growth_analytics, funnel, risk, merchant_perf, disputes_refunds, ad_hoc]
2. metrics: List of KPI names requested
3. time_window: Date range mentioned (or null for default 30 days)
4. group_by: Dimensions to break down by (merchant, city, cohort, etc.)
5. comparison: Whether comparing periods (true/false)

Respond in JSON format only."""),
            ("human", "{query}")
        ])
    
    async def __call__(self, state: AgentState) -> AgentState:
        """Process the user query and classify intent."""
        state.current_node = "router"
        query = state.user_query.lower()
        
        # 1. Classify intent
        state.intent = self._classify_intent(query)
        
        # 2. Extract entities
        state.entities = self._extract_entities(query)
        
        # 3. Use LLM for complex cases if available
        if state.intent == "ad_hoc" and self.llm:
            await self._llm_classify(state)
        
        return state
    
    def _classify_intent(self, query: str) -> str:
        """Rule-based intent classification."""
        scores = {}
        
        for intent, patterns in INTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    score += 1
            scores[intent] = score
        
        # Get intent with highest score
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                return best_intent[0]
        
        return "ad_hoc"
    
    def _extract_entities(self, query: str) -> QueryEntities:
        """Extract entities from query."""
        entities = QueryEntities()
        
        # Extract metrics
        for metric, patterns in METRIC_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query, re.IGNORECASE):
                    entities.metrics.append(metric)
                    break
        
        # Extract time window
        entities.time_window = self._extract_time_window(query)
        
        # Extract group_by dimensions
        entities.group_by = self._extract_group_by(query)
        
        # Check for comparison
        if re.search(r"\bvs\.?\b|\bcompare\b|\btrend\b|\bover\s*(time|month|week)\b", query, re.IGNORECASE):
            entities.comparison = True
        
        # Extract limit
        limit_match = re.search(r"\btop\s*(\d+)\b", query, re.IGNORECASE)
        if limit_match:
            entities.limit = int(limit_match.group(1))
        
        return entities
    
    def _extract_time_window(self, query: str) -> Optional[TimeRange]:
        """Extract time window from query."""
        today = datetime.now()
        
        # Last N days
        days_match = re.search(r"\blast\s*(\d+)\s*days?\b", query, re.IGNORECASE)
        if days_match:
            days = int(days_match.group(1))
            return TimeRange(
                start_date=(today - timedelta(days=days)).strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )
        
        # Last week
        if re.search(r"\blast\s*week\b", query, re.IGNORECASE):
            return TimeRange(
                start_date=(today - timedelta(days=7)).strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )
        
        # Last month
        if re.search(r"\blast\s*month\b", query, re.IGNORECASE):
            return TimeRange(
                start_date=(today - timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )
        
        # Last quarter / 90 days
        if re.search(r"\blast\s*(quarter|90\s*days)\b", query, re.IGNORECASE):
            return TimeRange(
                start_date=(today - timedelta(days=90)).strftime("%Y-%m-%d"),
                end_date=today.strftime("%Y-%m-%d"),
            )
        
        # Default: last 30 days
        return TimeRange(
            start_date=(today - timedelta(days=30)).strftime("%Y-%m-%d"),
            end_date=today.strftime("%Y-%m-%d"),
        )
    
    def _extract_group_by(self, query: str) -> list:
        """Extract grouping dimensions."""
        group_by = []
        
        if re.search(r"\bby\s*(merchant|store)\b", query, re.IGNORECASE):
            group_by.append("merchant_id")
        if re.search(r"\bby\s*city\b", query, re.IGNORECASE):
            group_by.append("city")
        if re.search(r"\bby\s*category\b", query, re.IGNORECASE):
            group_by.append("category")
        if re.search(r"\bby\s*cohort\b", query, re.IGNORECASE):
            group_by.append("signup_week")
        if re.search(r"\bby\s*day\b", query, re.IGNORECASE):
            group_by.append("date")
        
        return group_by
    
    async def _llm_classify(self, state: AgentState) -> None:
        """Use LLM for complex classification."""
        if not self.llm:
            return
        
        try:
            chain = self._router_prompt | self.llm
            response = await chain.ainvoke({"query": state.user_query})
            
            import json
            result = json.loads(response.content)
            
            if result.get("intent"):
                state.intent = result["intent"]
            if result.get("metrics"):
                state.entities.metrics.extend(result["metrics"])
            if result.get("group_by"):
                state.entities.group_by.extend(result["group_by"])
                
        except Exception:
            # Keep rule-based classification
            pass
