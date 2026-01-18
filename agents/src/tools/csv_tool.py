"""
CSV Tool - Safe, direct Pandas filtering for local CSV data.

Replaces the need for SQL emulation by allowing the agent to 
operate directly on DataFrames using structured filter logic.
"""

import json
import pandas as pd
from typing import Optional, List, Dict, Any, Union
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from .local_data import get_local_data

class CSVQuery(BaseModel):
    """Structure for a CSV query."""
    table: str = Field(description="Name of the table (csv file) to query")
    columns: List[str] = Field(default=["*"], description="Columns to select")
    filters: List[Dict[str, Any]] = Field(default=[], description="List of filters: {'col': 'age', 'op': '>', 'val': 18}")
    sort_by: Optional[str] = Field(default=None, description="Column to sort by")
    ascending: bool = Field(default=False, description="Sort direction")
    limit: int = Field(default=50, description="Max rows to return")

class CSVTool(BaseTool):
    """
    Tool for querying local CSV files using Pandas.
    
    Usage:
        tool = CSVTool()
        result = tool.run(json.dumps({
            "table": "users",
            "filters": [{"col": "risk_score", "op": "<", "val": 30}],
            "columns": ["user_id", "risk_score", "email"]
        }))
    """
    name: str = "csv_query"
    description: str = "Query local CSV files using structured filters."
    
    def _run(self, query_json: str) -> str:
        """Run the tool (sync)."""
        try:
            # Parse input
            if isinstance(query_json, dict):
                params = query_json
            else:
                params = json.loads(query_json)
                
            query = CSVQuery(**params)
            
            # Get data
            adapter = get_local_data()
            df = adapter.get_table(query.table)
            
            if df is None:
                return f"Error: Table '{query.table}' not found. Available: {', '.join(adapter.tables)}"
            
            # Apply filters
            filtered_df = df.copy()
            
            for f in query.filters:
                col = f.get("col")
                op = f.get("op", "==")
                val = f.get("val")
                
                if col not in filtered_df.columns:
                    continue
                    
                if op == "==":
                    filtered_df = filtered_df[filtered_df[col] == val]
                elif op == "!=":
                    filtered_df = filtered_df[filtered_df[col] != val]
                elif op == ">":
                    filtered_df = filtered_df[filtered_df[col] > val]
                elif op == ">=":
                    filtered_df = filtered_df[filtered_df[col] >= val]
                elif op == "<":
                    filtered_df = filtered_df[filtered_df[col] < val]
                elif op == "<=":
                    filtered_df = filtered_df[filtered_df[col] <= val]
                elif op == "contains":
                    filtered_df = filtered_df[filtered_df[col].astype(str).str.contains(str(val), case=False, na=False)]
                elif op == "in":
                    filtered_df = filtered_df[filtered_df[col].isin(val if isinstance(val, list) else [val])]
            
            # Select columns
            if query.columns and "*" not in query.columns:
                # Only select existing columns
                valid_cols = [c for c in query.columns if c in filtered_df.columns]
                if valid_cols:
                    filtered_df = filtered_df[valid_cols]
            
            # Sort
            if query.sort_by and query.sort_by in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by=query.sort_by, ascending=query.ascending)
            
            # Limit
            result_df = filtered_df.head(query.limit)
            
            # Format output
            return f"Found {len(result_df)} rows:\n\n" + result_df.to_markdown(index=False)
            
        except Exception as e:
            return f"CSV Query Error: {str(e)}"
            
    async def _arun(self, query_json: str) -> str:
        """Async run."""
        return self._run(query_json)
