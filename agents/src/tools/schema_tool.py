"""
Schema Tool - MCP wrapper for schema discovery.

Provides access to available tables, columns, and relationships
from the BNPL data warehouse Silver/Gold layers.
"""

import asyncio
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from .mcp_client import get_mcp_client, MCPResponse


class SchemaInfo(BaseModel):
    """Schema information for a table."""
    
    table_name: str
    columns: List[dict] = Field(default_factory=list)
    primary_key: Optional[str] = None
    foreign_keys: List[dict] = Field(default_factory=list)
    description: Optional[str] = None


class SchemaResult(BaseModel):
    """Result from schema discovery."""
    
    tables: List[SchemaInfo] = Field(default_factory=list)
    relationships: List[dict] = Field(default_factory=list)
    allowed_tables: List[str] = Field(default_factory=list)


class SchemaTool(BaseTool):
    """
    LangChain tool for discovering database schema via MCP.
    
    Returns allowed tables, columns, and relationships for the BNPL
    data warehouse. Agents use this to validate SQL queries.
    
    Usage:
        tool = SchemaTool()
        result = tool.invoke({})  # Get full schema
        result = tool.invoke({"table_name": "orders"})  # Get specific table
    """
    
    name: str = "schema_get"
    description: str = """Get database schema information including tables, columns, and relationships.
    Use this tool BEFORE generating SQL queries to understand available data.
    
    Input: Optional table_name to get schema for a specific table.
    Output: List of tables with columns, types, and relationships.
    
    Allowed tables for AI agents (Gold layer preferred):
    - kpi_daily: Daily KPIs (gmv, approval_rate, late_rate, etc.)
    - user_features_daily: User-level features
    - merchant_features_daily: Merchant-level features  
    - cohorts_signup_week: Cohort analysis
    
    Silver layer (for drill-downs only):
    - orders, installments, payments, users, merchants, disputes_returns
    """
    
    # Default schema based on repository documentation
    _default_schema: dict = {
        "gold": {
            "kpi_daily": {
                "columns": ["date", "gmv", "approval_rate", "late_rate", "dispute_rate", "net_margin"],
                "description": "Daily aggregated KPIs"
            },
            "user_features_daily": {
                "columns": ["user_id", "date", "on_time_rate_30d", "on_time_rate_90d", 
                           "late_days_sum_30d", "late_days_sum_90d", "installment_count_90d",
                           "avg_installment_amount_30d", "device_change_count_30d", 
                           "dispute_rate_90d", "account_age_days"],
                "description": "User-level features (one row per user per day)"
            },
            "merchant_features_daily": {
                "columns": ["merchant_id", "date", "approval_rate_30d", "late_rate_30d",
                           "dispute_rate_30d", "refund_rate_30d", "order_count_30d", "gmv_30d"],
                "description": "Merchant-level features (one row per merchant per day)"
            },
            "cohorts_signup_week": {
                "columns": ["signup_week", "user_count", "late_rate_30d", "avg_order_amount"],
                "description": "User cohort analysis by signup week"
            }
        },
        "silver": {
            "users": {
                "columns": ["user_id", "signup_date", "kyc_level", "city", 
                           "device_fingerprint", "account_status"],
                "description": "User master data"
            },
            "merchants": {
                "columns": ["merchant_id", "merchant_name", "category", "city", "risk_tier"],
                "description": "Merchant master data"
            },
            "orders": {
                "columns": ["order_id", "user_id", "merchant_id", "amount", 
                           "currency", "status", "created_at"],
                "description": "BNPL orders"
            },
            "installments": {
                "columns": ["installment_id", "order_id", "due_date", "paid_date", 
                           "status", "late_days"],
                "description": "Payment installments"
            },
            "payments": {
                "columns": ["payment_id", "installment_id", "amount", 
                           "payment_channel", "paid_at"],
                "description": "Actual payments made"
            },
            "disputes_returns": {
                "columns": ["case_id", "order_id", "reason", "amount", "outcome"],
                "description": "Disputes and refunds"
            }
        }
    }
    
    def _run(self, table_name: Optional[str] = None) -> str:
        """Synchronous schema fetch."""
        return asyncio.run(self._arun(table_name))
    
    async def _arun(self, table_name: Optional[str] = None) -> str:
        """
        Fetch schema from MCP server.
        
        Falls back to default schema if MCP is unavailable.
        """
        client = get_mcp_client()
        
        params = {}
        if table_name:
            params["table_name"] = table_name
        
        response: MCPResponse = await client.call("schema.get", params)
        
        if response.success and response.data:
            return self._format_schema(response.data, table_name)
        
        # Fallback to default schema
        return self._format_default_schema(table_name)
    
    def _format_schema(self, data: dict, table_name: Optional[str] = None) -> str:
        """Format MCP schema response as readable text."""
        lines = ["# Available Schema\n"]
        
        tables = data.get("tables", [])
        if table_name:
            tables = [t for t in tables if t.get("name") == table_name]
        
        for table in tables:
            lines.append(f"## {table.get('name', 'Unknown')}")
            lines.append(f"Description: {table.get('description', 'N/A')}")
            lines.append("Columns:")
            for col in table.get("columns", []):
                col_name = col.get("name", "")
                col_type = col.get("type", "")
                lines.append(f"  - {col_name} ({col_type})")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_default_schema(self, table_name: Optional[str] = None) -> str:
        """Format default schema as readable text."""
        lines = ["# Available Schema (from configuration)\n"]
        
        for layer, tables in self._default_schema.items():
            if table_name and table_name not in tables:
                continue
                
            lines.append(f"## {layer.upper()} Layer\n")
            
            for tbl_name, info in tables.items():
                if table_name and tbl_name != table_name:
                    continue
                    
                lines.append(f"### {tbl_name}")
                lines.append(f"{info.get('description', '')}")
                lines.append("Columns: " + ", ".join(info.get("columns", [])))
                lines.append("")
        
        return "\n".join(lines)
    
    def get_allowed_tables(self) -> List[str]:
        """Get list of all allowed table names."""
        tables = []
        for layer in self._default_schema.values():
            tables.extend(layer.keys())
        return tables
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get columns for a specific table."""
        for layer in self._default_schema.values():
            if table_name in layer:
                return layer[table_name].get("columns", [])
        return []
