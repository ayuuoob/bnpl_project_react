"""
Tests for the Router node.
"""

import pytest
from src.nodes.router import RouterNode
from src.state import AgentState


class TestRouterNode:
    """Test cases for intent classification and entity extraction."""
    
    @pytest.fixture
    def router(self):
        """Create router instance without LLM."""
        return RouterNode(llm=None)
    
    @pytest.mark.asyncio
    async def test_growth_intent_gmv(self, router):
        """Test GMV query is classified as growth_analytics."""
        state = AgentState(user_query="What was our GMV last month?")
        result = await router(state)
        
        assert result.intent == "growth_analytics"
        assert "gmv" in result.entities.metrics
    
    @pytest.mark.asyncio
    async def test_growth_intent_active_users(self, router):
        """Test active users query is classified as growth_analytics."""
        state = AgentState(user_query="How many active users do we have?")
        result = await router(state)
        
        assert result.intent == "growth_analytics"
        assert "active_users" in result.entities.metrics
    
    @pytest.mark.asyncio
    async def test_risk_intent_late_rate(self, router):
        """Test late rate query is classified as risk."""
        state = AgentState(user_query="What is our late payment rate by cohort?")
        result = await router(state)
        
        assert result.intent == "risk"
        assert "late_rate" in result.entities.metrics
    
    @pytest.mark.asyncio
    async def test_merchant_intent(self, router):
        """Test merchant query is classified as merchant_perf."""
        state = AgentState(user_query="Which merchants have the highest dispute rates?")
        result = await router(state)
        
        assert result.intent in ["merchant_perf", "disputes_refunds"]
    
    @pytest.mark.asyncio
    async def test_funnel_intent(self, router):
        """Test conversion query is classified as funnel."""
        state = AgentState(user_query="What is our checkout conversion rate?")
        result = await router(state)
        
        assert result.intent == "funnel"
    
    @pytest.mark.asyncio
    async def test_time_window_extraction_last_month(self, router):
        """Test time window extraction for 'last month'."""
        state = AgentState(user_query="What was our GMV last month?")
        result = await router(state)
        
        assert result.entities.time_window is not None
        assert result.entities.time_window.start_date is not None
        assert result.entities.time_window.end_date is not None
    
    @pytest.mark.asyncio
    async def test_group_by_extraction(self, router):
        """Test group_by dimension extraction."""
        state = AgentState(user_query="What is our GMV by merchant?")
        result = await router(state)
        
        assert "merchant_id" in result.entities.group_by
    
    @pytest.mark.asyncio
    async def test_comparison_detection(self, router):
        """Test comparison period detection."""
        state = AgentState(user_query="What was our GMV last month vs previous month?")
        result = await router(state)
        
        assert result.entities.comparison is True
    
    @pytest.mark.asyncio
    async def test_limit_extraction(self, router):
        """Test top N limit extraction."""
        state = AgentState(user_query="Who are our top 10 merchants by GMV?")
        result = await router(state)
        
        assert result.entities.limit == 10
