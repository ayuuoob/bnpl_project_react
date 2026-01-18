"""
KPI Handler - Business Metrics Queries

Handles queries about GMV, approval rate, order counts, etc.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any

from ..state import AgentState


class KPIHandler:
    """Handler for KPI/business metrics queries."""
    
    def __init__(self, data_path: str = "../data"):
        self.data_path = Path(data_path)
        self._orders_df = None
        self._analytics_df = None
    
    @property
    def orders_df(self) -> pd.DataFrame:
        """Lazy load orders data."""
        if self._orders_df is None:
            path = self.data_path / "silver" / "orders.csv"
            if path.exists():
                self._orders_df = pd.read_csv(path)
            else:
                self._orders_df = pd.DataFrame()
        return self._orders_df
    
    @property
    def analytics_df(self) -> pd.DataFrame:
        """Lazy load gold analytics data."""
        if self._analytics_df is None:
            path = self.data_path / "gold" / "gold_orders_analytics.csv"
            if path.exists():
                self._analytics_df = pd.read_csv(path)
            else:
                self._analytics_df = pd.DataFrame()
        return self._analytics_df
    
    async def handle(self, state: AgentState) -> AgentState:
        """Handle KPI query and populate state with data."""
        query_lower = state.user_query.lower()
        
        try:
            # Determine which KPI to compute
            if "gmv" in query_lower or "revenue" in query_lower:
                state.data = self._compute_gmv()
            elif "approval" in query_lower:
                state.data = self._compute_approval_rate()
            elif "late" in query_lower or "delinquency" in query_lower:
                state.data = self._compute_late_rate()
            elif "order" in query_lower and "count" in query_lower:
                state.data = self._compute_order_count()
            elif "user" in query_lower and ("count" in query_lower or "active" in query_lower):
                state.data = self._compute_active_users()
            elif "dispute" in query_lower:
                state.data = self._compute_dispute_stats()
            elif "kpi" in query_lower or "overview" in query_lower or "summary" in query_lower:
                state.data = self._compute_all_kpis()
            else:
                # Default to all KPIs
                state.data = self._compute_all_kpis()
                
        except Exception as e:
            state.error = f"Error computing KPI: {str(e)}"
        
        return state
    
    def _compute_gmv(self) -> Dict[str, Any]:
        """Compute Gross Merchandise Value."""
        df = self.orders_df
        if df.empty:
            return {"metric": "GMV", "value": 0, "currency": "MAD"}
        
        approved = df[df["status"] == "approved"] if "status" in df.columns else df
        gmv = approved["amount"].sum() if "amount" in df.columns else 0
        
        return {
            "metric": "GMV",
            "value": round(gmv, 2),
            "currency": "MAD",
            "total_orders": len(approved),
            "description": "Total approved order value"
        }
    
    def _compute_approval_rate(self) -> Dict[str, Any]:
        """Compute order approval rate."""
        df = self.orders_df
        if df.empty or "status" not in df.columns:
            return {"metric": "Approval Rate", "value": 0, "formatted": "0%"}
        
        total = len(df)
        approved = len(df[df["status"] == "approved"])
        rate = (approved / total * 100) if total > 0 else 0
        
        return {
            "metric": "Approval Rate",
            "value": round(rate, 2),
            "formatted": f"{rate:.1f}%",
            "approved_count": approved,
            "total_count": total
        }
    
    def _compute_late_rate(self) -> Dict[str, Any]:
        """Compute late payment rate from installments."""
        path = self.data_path / "silver" / "installments.csv"
        if not path.exists():
            return {"metric": "Late Payment Rate", "value": 0, "formatted": "0%"}
        
        df = pd.read_csv(path)
        if "status" not in df.columns:
            return {"metric": "Late Payment Rate", "value": 0, "formatted": "0%"}
        
        total = len(df[df["status"].isin(["paid", "late"])])
        late = len(df[df["status"] == "late"])
        rate = (late / total * 100) if total > 0 else 0
        
        return {
            "metric": "Late Payment Rate",
            "value": round(rate, 2),
            "formatted": f"{rate:.1f}%",
            "late_count": late,
            "total_evaluated": total
        }
    
    def _compute_order_count(self) -> Dict[str, Any]:
        """Compute total order count."""
        df = self.orders_df
        return {
            "metric": "Total Orders",
            "value": len(df),
            "by_status": df["status"].value_counts().to_dict() if "status" in df.columns else {}
        }
    
    def _compute_active_users(self) -> Dict[str, Any]:
        """Compute active user count."""
        path = self.data_path / "silver" / "users.csv"
        if not path.exists():
            return {"metric": "Active Users", "value": 0}
        
        df = pd.read_csv(path)
        total = len(df)
        active = len(df[df["account_status"] == "active"]) if "account_status" in df.columns else total
        
        return {
            "metric": "Active Users",
            "value": active,
            "total_users": total,
            "by_status": df["account_status"].value_counts().to_dict() if "account_status" in df.columns else {}
        }
    
    def _compute_dispute_stats(self) -> Dict[str, Any]:
        """Compute dispute statistics."""
        path = self.data_path / "silver" / "disputes.csv"
        if not path.exists():
            return {"metric": "Disputes", "value": 0}
        
        df = pd.read_csv(path)
        return {
            "metric": "Disputes",
            "value": len(df),
            "by_reason": df["reason"].value_counts().to_dict() if "reason" in df.columns else {}
        }
    
    def _compute_all_kpis(self) -> Dict[str, Any]:
        """Compute all KPIs for overview."""
        return {
            "type": "kpi_overview",
            "metrics": {
                "gmv": self._compute_gmv(),
                "approval_rate": self._compute_approval_rate(),
                "late_rate": self._compute_late_rate(),
                "orders": self._compute_order_count(),
                "users": self._compute_active_users(),
                "disputes": self._compute_dispute_stats()
            }
        }
