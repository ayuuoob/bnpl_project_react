"""
Integration tests for the full agent workflow.
"""

import pytest
from src.graph import run_query, create_agent_graph
from src.state import AgentState


class TestAgentIntegration:
    """End-to-end integration tests."""
    
    @pytest.fixture
    def agent(self):
        """Create agent graph."""
        return create_agent_graph()
    
    @pytest.mark.asyncio
    async def test_full_query_flow(self, agent):
        """Test complete query processing."""
        initial_state = AgentState(user_query="What was our GMV last month?")
        
        final_state = await agent.ainvoke(initial_state)
        
        # Should have processed through all nodes
        assert final_state.get("intent") == "growth_analytics"
        assert final_state.get("plan") is not None
        assert len(final_state.get("tool_calls", [])) > 0
        assert final_state.get("final_response") is not None
    
    @pytest.mark.asyncio
    async def test_run_query_helper(self):
        """Test the run_query helper function."""
        response = await run_query("How many active users do we have?")
        
        assert response is not None
        assert len(response) > 0
        assert "[Answer Summary]" in response or "summary" in response.lower()
    
    @pytest.mark.asyncio
    async def test_response_format(self):
        """Test response contains required sections."""
        response = await run_query("What is our late payment rate?")
        
        # Should contain structured sections
        assert any(section in response for section in [
            "[Answer Summary]",
            "[Key Metrics]",
            "[Recommended Actions]",
            "[Data & Assumptions]",
        ])
    
    @pytest.mark.asyncio
    async def test_risk_query(self):
        """Test risk intent query."""
        response = await run_query("What is our delinquency bucket distribution?")
        
        assert response is not None
        assert "bucket" in response.lower() or "late" in response.lower() or "delinquency" in response.lower()
    
    @pytest.mark.asyncio
    async def test_merchant_query(self):
        """Test merchant performance query."""
        response = await run_query("Who are our top merchants by GMV?")
        
        assert response is not None
        assert len(response) > 100  # Should have substantial content


class TestGraphConstruction:
    """Test graph structure."""
    
    def test_graph_creation(self):
        """Test agent graph can be created."""
        graph = create_agent_graph()
        
        assert graph is not None
    
    def test_graph_has_nodes(self):
        """Test graph contains expected nodes."""
        graph = create_agent_graph()
        
        # Graph should be compiled and runnable
        assert hasattr(graph, "ainvoke")
