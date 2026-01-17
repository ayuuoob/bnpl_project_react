"""
Tests for MCP Tool wrappers.
"""

import pytest
from src.tools import SchemaTool, KPITool, SQLTool


class TestSchemaTool:
    """Test cases for Schema tool."""
    
    @pytest.fixture
    def schema_tool(self):
        return SchemaTool()
    
    def test_get_allowed_tables(self, schema_tool):
        """Test getting allowed table list."""
        tables = schema_tool.get_allowed_tables()
        
        assert "orders" in tables
        assert "users" in tables
        assert "kpi_daily" in tables
        assert "installments" in tables
    
    def test_get_table_columns(self, schema_tool):
        """Test getting columns for a table."""
        columns = schema_tool.get_table_columns("orders")
        
        assert "order_id" in columns
        assert "user_id" in columns
        assert "amount" in columns
        assert "status" in columns
    
    @pytest.mark.asyncio
    async def test_schema_fallback(self, schema_tool):
        """Test schema returns data even without MCP."""
        result = await schema_tool._arun()
        
        assert "Available Schema" in result
        assert "orders" in result.lower()


class TestKPITool:
    """Test cases for KPI tool."""
    
    @pytest.fixture
    def kpi_tool(self):
        return KPITool()
    
    @pytest.mark.asyncio
    async def test_valid_kpi_name(self, kpi_tool):
        """Test fetching a valid KPI."""
        result = await kpi_tool._arun(kpi_name="gmv")
        
        assert "GMV" in result
        assert "Value:" in result
    
    @pytest.mark.asyncio
    async def test_invalid_kpi_name(self, kpi_tool):
        """Test error for invalid KPI."""
        result = await kpi_tool._arun(kpi_name="invalid_kpi_xyz")
        
        assert "Error" in result
        assert "Unknown KPI" in result
    
    @pytest.mark.asyncio
    async def test_kpi_with_date_range(self, kpi_tool):
        """Test KPI with custom date range."""
        result = await kpi_tool._arun(
            kpi_name="approval_rate",
            start_date="2025-12-01",
            end_date="2025-12-31",
        )
        
        assert "approval_rate" in result.lower()
        assert "2025-12-01" in result
    
    def test_list_kpis(self):
        """Test listing all available KPIs."""
        result = KPITool.list_kpis()
        
        assert "gmv" in result.lower()
        assert "late_rate" in result.lower()
        assert "dispute_rate" in result.lower()


class TestSQLTool:
    """Test cases for SQL tool."""
    
    @pytest.fixture
    def sql_tool(self):
        return SQLTool()
    
    @pytest.mark.asyncio
    async def test_valid_select_query(self, sql_tool):
        """Test valid SELECT query."""
        result = await sql_tool._arun(
            query="SELECT merchant_id, COUNT(*) FROM orders WHERE created_at >= '2025-12-01' GROUP BY merchant_id"
        )
        
        # Should return mock data (MCP not connected)
        assert "mock data" in result.lower() or "rows" in result.lower()
    
    @pytest.mark.asyncio
    async def test_blocked_insert_query(self, sql_tool):
        """Test INSERT query is blocked."""
        result = await sql_tool._arun(
            query="INSERT INTO orders VALUES (1, 2, 3)"
        )
        
        assert "Validation Failed" in result
        assert "SELECT" in result
    
    @pytest.mark.asyncio
    async def test_blocked_delete_query(self, sql_tool):
        """Test DELETE query is blocked."""
        result = await sql_tool._arun(
            query="DELETE FROM orders WHERE id = 1"
        )
        
        assert "Validation Failed" in result
    
    @pytest.mark.asyncio
    async def test_invalid_table(self, sql_tool):
        """Test query with non-allowed table."""
        result = await sql_tool._arun(
            query="SELECT * FROM secret_table"
        )
        
        assert "Validation Failed" in result or "not in the allowlist" in result
