"""
KPI Tool - MCP wrapper for fetching pre-computed KPIs.

Provides access to templated KPI calculations from the Gold layer.
This is the PREFERRED way to get metrics (vs raw SQL).
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from .mcp_client import get_mcp_client, MCPResponse


class KPIDefinition(BaseModel):
    """Definition of a KPI template."""
    
    name: str
    description: str
    formula: str
    tables: List[str]
    dimensions: List[str] = Field(default_factory=list)
    default_time_window: int = 30  # days


class KPIResult(BaseModel):
    """Result from KPI calculation."""
    
    kpi_name: str
    value: float
    time_range: dict
    breakdown: Optional[List[dict]] = None
    metadata: dict = Field(default_factory=dict)


# KPI definitions based on implementation plan
KPI_CATALOG = {
    "gmv": KPIDefinition(
        name="gmv",
        description="Gross Merchandise Value - Total value of approved orders",
        formula="SUM(amount) WHERE status='approved'",
        tables=["orders", "kpi_daily"],
        dimensions=["date", "merchant_id", "city", "category"],
    ),
    "approval_rate": KPIDefinition(
        name="approval_rate",
        description="Percentage of orders approved",
        formula="COUNT(approved) / COUNT(total)",
        tables=["orders", "kpi_daily"],
        dimensions=["date", "merchant_id", "category"],
    ),
    "active_users": KPIDefinition(
        name="active_users",
        description="Count of distinct users with orders in time window",
        formula="COUNT(DISTINCT user_id) with order in period",
        tables=["orders", "users"],
        dimensions=["date", "city", "cohort"],
    ),
    "repeat_user_rate": KPIDefinition(
        name="repeat_user_rate",
        description="Percentage of users with 2+ orders",
        formula="COUNT(users with 2+ orders) / COUNT(all users)",
        tables=["orders"],
        dimensions=["date", "cohort", "city"],
    ),
    "late_rate": KPIDefinition(
        name="late_rate",
        description="Late Payment Rate - Percentage of late installments",
        formula="COUNT(late installments) / COUNT(total installments)",
        tables=["installments", "kpi_daily"],
        dimensions=["date", "user_cohort", "merchant_id"],
    ),
    "delinquency_buckets": KPIDefinition(
        name="delinquency_buckets",
        description="Count of installments by late days buckets",
        formula="COUNT by late_days: 1-7, 8-30, 31-60, 60+",
        tables=["installments"],
        dimensions=["date", "cohort"],
    ),
    "dispute_rate": KPIDefinition(
        name="dispute_rate",
        description="Dispute Rate - Disputes per order",
        formula="COUNT(disputes) / COUNT(orders)",
        tables=["disputes_returns", "orders", "kpi_daily"],
        dimensions=["date", "merchant_id", "category"],
    ),
    "refund_rate": KPIDefinition(
        name="refund_rate",
        description="Refund Rate - Refund amount as % of GMV",
        formula="SUM(refund_amount) / SUM(gmv)",
        tables=["disputes_returns", "orders"],
        dimensions=["date", "merchant_id"],
    ),
    "checkout_conversion": KPIDefinition(
        name="checkout_conversion",
        description="Checkout Conversion Rate",
        formula="COUNT(ORDER_OK) / COUNT(checkout_start)",
        tables=["checkout_events"],
        dimensions=["date", "merchant_id", "device"],
    ),
    "repayment_velocity": KPIDefinition(
        name="repayment_velocity",
        description="Average days early/late for payments",
        formula="AVG(paid_date - due_date)",
        tables=["installments", "payments"],
        dimensions=["date", "cohort"],
    ),
}


class KPITool(BaseTool):
    """
    LangChain tool for fetching pre-computed KPIs via MCP.
    
    This is the PREFERRED method for getting metrics. Use SQL only
    for drill-downs or non-standard queries.
    
    Usage:
        tool = KPITool()
        result = tool.invoke({
            "kpi_name": "gmv",
            "start_date": "2025-12-01",
            "end_date": "2025-12-31",
            "group_by": ["merchant_id"]
        })
    """
    
    name: str = "kpi_get"
    description: str = """Fetch pre-computed KPI values from the data warehouse.
    
    Available KPIs:
    - gmv: Gross Merchandise Value (total approved order value)
    - approval_rate: Order approval percentage
    - active_users: Distinct users with orders in period
    - repeat_user_rate: Users with 2+ orders
    - late_rate: Late payment percentage
    - delinquency_buckets: Count by late days (1-7, 8-30, 30+)
    - dispute_rate: Disputes per order
    - refund_rate: Refunds as % of GMV
    - checkout_conversion: Checkout to order conversion
    - repayment_velocity: Avg days early/late for payments
    
    Parameters:
    - kpi_name (required): Name of KPI to fetch
    - start_date: Start of time window (default: 30 days ago)
    - end_date: End of time window (default: today)
    - group_by: List of dimensions for breakdown (e.g., ["merchant_id", "city"])
    - filters: Dict of filters (e.g., {"merchant_id": "M001"})
    
    Returns: KPI value with optional breakdown by dimensions.
    """
    
    def _run(
        self,
        kpi_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: Optional[List[str]] = None,
        filters: Optional[dict] = None,
    ) -> str:
        """Synchronous KPI fetch."""
        return asyncio.run(self._arun(kpi_name, start_date, end_date, group_by, filters))
    
    async def _arun(
        self,
        kpi_name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        group_by: Optional[List[str]] = None,
        filters: Optional[dict] = None,
    ) -> str:
        """
        Fetch KPI from MCP server.
        
        Falls back to mock data if MCP is unavailable.
        """
        # Validate KPI name
        if kpi_name not in KPI_CATALOG:
            available = ", ".join(KPI_CATALOG.keys())
            return f"Error: Unknown KPI '{kpi_name}'. Available KPIs: {available}"
        
        # Set default date range
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if not start_date:
            start_dt = datetime.now() - timedelta(days=30)
            start_date = start_dt.strftime("%Y-%m-%d")
        
        # Build MCP request
        client = get_mcp_client()
        params = {
            "kpi_name": kpi_name,
            "date_range": {
                "start": start_date,
                "end": end_date,
            },
        }
        if group_by:
            params["group_by"] = group_by
        if filters:
            params["filters"] = filters
        
        response: MCPResponse = await client.call("kpi.get", params)
        
        if response.success and response.data:
            return self._format_result(kpi_name, response.data, start_date, end_date)
        
        # Fallback to mock data for development/demo
        mock_result = self._get_mock_result(kpi_name, start_date, end_date, group_by)
        return self._format_result(kpi_name, mock_result, start_date, end_date)
    
    def _format_result(
        self, 
        kpi_name: str, 
        data: dict, 
        start_date: str, 
        end_date: str
    ) -> str:
        """Format KPI result as readable text."""
        kpi_def = KPI_CATALOG.get(kpi_name)
        
        lines = [
            f"# KPI: {kpi_def.name.upper()}",
            f"Description: {kpi_def.description}",
            f"Time Range: {start_date} to {end_date}",
            "",
        ]
        
        # Main value
        value = data.get("value")
        if isinstance(value, float):
            if "rate" in kpi_name or "conversion" in kpi_name:
                lines.append(f"**Value: {value:.2%}**")
            else:
                lines.append(f"**Value: {value:,.2f}**")
        else:
            lines.append(f"**Value: {value}**")
        
        # Breakdown if available
        breakdown = data.get("breakdown", [])
        if breakdown:
            lines.append("\n## Breakdown:")
            for item in breakdown[:10]:  # Limit to top 10
                dim_value = item.get("dimension_value", "Unknown")
                metric_value = item.get("value", 0)
                if isinstance(metric_value, float):
                    if "rate" in kpi_name:
                        lines.append(f"  - {dim_value}: {metric_value:.2%}")
                    else:
                        lines.append(f"  - {dim_value}: {metric_value:,.2f}")
                else:
                    lines.append(f"  - {dim_value}: {metric_value}")
        
        # Metadata
        lines.append(f"\n_Tables used: {', '.join(kpi_def.tables)}_")
        lines.append(f"_Formula: {kpi_def.formula}_")
        
        return "\n".join(lines)
    
    def _get_mock_result(
        self,
        kpi_name: str,
        start_date: str,
        end_date: str,
        group_by: Optional[List[str]] = None,
    ) -> dict:
        """
        Get KPI result from local CSV data if available,
        otherwise generate mock data for demo.
        """
        import os
        
        # Try to use local data if enabled
        if os.getenv("USE_LOCAL_DATA", "true").lower() == "true":
            try:
                from .local_data import get_local_data
                local_data = get_local_data()
                
                if local_data.tables:  # Data loaded successfully
                    return self._calculate_from_local_data(
                        local_data, kpi_name, start_date, end_date, group_by
                    )
            except Exception as e:
                print(f"Warning: Could not use local data: {e}")
        
        # Fallback to mock data
        return self._generate_mock_data(kpi_name, group_by)
    
    def _calculate_from_local_data(
        self,
        local_data,
        kpi_name: str,
        start_date: str,
        end_date: str,
        group_by: Optional[List[str]] = None,
    ) -> dict:
        """Calculate KPI from local CSV data."""
        
        if kpi_name == "gmv":
            result = local_data.calculate_gmv(start_date, end_date)
            if group_by and "merchant_id" in group_by:
                top_merchants = local_data.get_top_merchants("gmv", 5)
                if not top_merchants.empty:
                    result["breakdown"] = [
                        {"dimension_value": row.get("merchant_name", row.get("merchant_id")), 
                         "value": row["gmv"]}
                        for _, row in top_merchants.iterrows()
                    ]
            return result
        
        elif kpi_name == "approval_rate":
            return local_data.calculate_approval_rate(start_date, end_date)
        
        elif kpi_name == "late_rate":
            return local_data.calculate_late_rate(start_date, end_date)
        
        elif kpi_name == "active_users":
            return local_data.calculate_active_users(start_date, end_date)
        
        elif kpi_name == "delinquency_buckets":
            buckets = local_data.get_delinquency_buckets()
            if not buckets.empty:
                return {
                    "value": "See breakdown",
                    "breakdown": [
                        {"dimension_value": row["bucket"], "value": row["count"]}
                        for _, row in buckets.iterrows()
                    ]
                }
            return {"value": "No late installments found"}
        
        else:
            # Fallback for other KPIs
            return self._generate_mock_data(kpi_name, group_by)
    
    def _generate_mock_data(
        self, 
        kpi_name: str, 
        group_by: Optional[List[str]] = None
    ) -> dict:
        """Generate mock data for demo/testing."""
        import random
        
        mock_values = {
            "gmv": {"value": random.uniform(1_500_000, 3_000_000)},
            "approval_rate": {"value": random.uniform(0.75, 0.92)},
            "active_users": {"value": random.randint(15000, 35000)},
            "repeat_user_rate": {"value": random.uniform(0.30, 0.45)},
            "late_rate": {"value": random.uniform(0.03, 0.08)},
            "dispute_rate": {"value": random.uniform(0.005, 0.02)},
            "refund_rate": {"value": random.uniform(0.01, 0.04)},
            "checkout_conversion": {"value": random.uniform(0.55, 0.75)},
            "repayment_velocity": {"value": random.uniform(-2, 3)},
            "delinquency_buckets": {
                "value": "See breakdown",
                "breakdown": [
                    {"dimension_value": "1-7 days", "value": random.randint(500, 1500)},
                    {"dimension_value": "8-30 days", "value": random.randint(200, 800)},
                    {"dimension_value": "31-60 days", "value": random.randint(50, 300)},
                    {"dimension_value": "60+ days", "value": random.randint(10, 100)},
                ]
            },
        }
        
        result = mock_values.get(kpi_name, {"value": 0})
        
        # Add mock breakdown if group_by requested
        if group_by and "breakdown" not in result:
            result["breakdown"] = [
                {"dimension_value": f"Group_{i+1}", "value": random.uniform(0.1, 0.5) * result.get("value", 1000)}
                for i in range(5)
            ]
        
        return result
    
    @classmethod
    def list_kpis(cls) -> str:
        """Get list of all available KPIs."""
        lines = ["# Available KPIs\n"]
        for name, kpi in KPI_CATALOG.items():
            lines.append(f"## {name}")
            lines.append(f"- Description: {kpi.description}")
            lines.append(f"- Formula: {kpi.formula}")
            lines.append(f"- Dimensions: {', '.join(kpi.dimensions)}")
            lines.append("")
        return "\n".join(lines)
