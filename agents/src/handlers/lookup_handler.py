"""
Lookup Handler - Data Queries

Handles queries for users, merchants, orders, and other data lookups.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from ..state import AgentState


class LookupHandler:
    """Handler for data lookup queries."""
    
    def __init__(self, data_path: str = "../data"):
        self.data_path = Path(data_path)
        self._cache = {}
    
    def _load_csv(self, name: str) -> pd.DataFrame:
        """Load and cache a CSV file."""
        if name not in self._cache:
            # Try silver first, then gold
            silver_path = self.data_path / "silver" / f"{name}.csv"
            gold_path = self.data_path / "gold" / f"{name}.csv"
            
            if silver_path.exists():
                self._cache[name] = pd.read_csv(silver_path)
            elif gold_path.exists():
                self._cache[name] = pd.read_csv(gold_path)
            else:
                self._cache[name] = pd.DataFrame()
        
        return self._cache[name]
    
    async def handle(self, state: AgentState) -> AgentState:
        """Handle lookup query and populate state with data."""
        query_lower = state.user_query.lower()
        entities = state.entities
        
        try:
            # Specific user lookup
            if entities.user_id:
                state.data = self._lookup_user(entities.user_id)
            
            # Specific merchant lookup
            elif entities.merchant_id:
                state.data = self._lookup_merchant(entities.merchant_id)
            
            # Specific order lookup
            elif entities.order_id:
                state.data = self._lookup_order(entities.order_id)
            
            # User list (with optional filters)
            elif "user" in query_lower:
                state.data = self._list_users(
                    city=entities.city,
                    limit=entities.limit or 20
                )
            
            # Merchant list
            elif "merchant" in query_lower:
                state.data = self._list_merchants(
                    category=entities.category,
                    limit=entities.limit or 20
                )
            
            # Order list
            elif "order" in query_lower:
                state.data = self._list_orders(
                    status=entities.status,
                    category=entities.category,
                    time_period=entities.time_period,
                    limit=entities.limit or 20
                )
            
            # Installment list
            elif "installment" in query_lower:
                state.data = self._list_installments(
                    status=entities.status,
                    limit=entities.limit or 20
                )
            
            # Category breakdown
            elif "category" in query_lower or "categories" in query_lower:
                state.data = self._get_category_breakdown()
            
            # City breakdown
            elif "city" in query_lower or "cities" in query_lower:
                state.data = self._get_city_breakdown()
            
            # Default
            else:
                state.data = {"type": "lookup", "message": "Please specify what you'd like to look up"}
                
        except Exception as e:
            state.error = f"Error in lookup: {str(e)}"
        
        return state
    
    def _lookup_user(self, user_id: str) -> Dict[str, Any]:
        """Look up a specific user."""
        df = self._load_csv("users")
        
        if df.empty:
            return {"type": "user_lookup", "error": "Users data not available"}
        
        row = df[df["user_id"] == user_id]
        if row.empty:
            return {"type": "user_lookup", "error": f"User {user_id} not found"}
        
        user = row.iloc[0].to_dict()
        
        # Get user's orders
        orders_df = self._load_csv("orders")
        user_orders = orders_df[orders_df["user_id"] == user_id] if not orders_df.empty else pd.DataFrame()
        
        return {
            "type": "user_lookup",
            "user": {k: str(v) if pd.notna(v) else None for k, v in user.items()},
            "order_count": len(user_orders),
            "total_amount": round(user_orders["amount"].sum(), 2) if not user_orders.empty else 0,
            "items": [{k: str(v) if pd.notna(v) else None for k, v in user.items()}]
        }
    
    def _lookup_merchant(self, merchant_id: str) -> Dict[str, Any]:
        """Look up a specific merchant."""
        df = self._load_csv("merchants")
        
        if df.empty:
            return {"type": "merchant_lookup", "error": "Merchants data not available"}
        
        row = df[df["merchant_id"] == merchant_id]
        if row.empty:
            return {"type": "merchant_lookup", "error": f"Merchant {merchant_id} not found"}
        
        merchant = row.iloc[0].to_dict()
        
        # Get merchant's orders
        orders_df = self._load_csv("orders")
        merchant_orders = orders_df[orders_df["merchant_id"] == merchant_id] if not orders_df.empty else pd.DataFrame()
        
        return {
            "type": "merchant_lookup",
            "merchant": {k: str(v) if pd.notna(v) else None for k, v in merchant.items()},
            "order_count": len(merchant_orders),
            "gmv": round(merchant_orders[merchant_orders["status"] == "approved"]["amount"].sum(), 2) if not merchant_orders.empty else 0
        }
    
    def _lookup_order(self, order_id: str) -> Dict[str, Any]:
        """Look up a specific order."""
        df = self._load_csv("orders")
        
        if df.empty:
            return {"type": "order_lookup", "error": "Orders data not available"}
        
        row = df[df["order_id"] == order_id]
        if row.empty:
            return {"type": "order_lookup", "error": f"Order {order_id} not found"}
        
        order = row.iloc[0].to_dict()
        
        return {
            "type": "order_lookup",
            "order": {k: str(v) if pd.notna(v) else None for k, v in order.items()}
        }
    
    def _list_users(self, city: str = None, limit: int = 20) -> Dict[str, Any]:
        """List users with optional filters."""
        df = self._load_csv("users")
        
        if df.empty:
            return {"type": "user_list", "items": []}
        
        # Apply filters
        if city and "city" in df.columns:
            df = df[df["city"].str.lower() == city.lower()]
        
        # Limit and format
        df = df.head(limit)
        items = df.to_dict("records")
        
        return {
            "type": "user_list",
            "count": len(items),
            "filters": {"city": city} if city else {},
            "items": items
        }
    
    def _list_merchants(self, category: str = None, limit: int = 20) -> Dict[str, Any]:
        """List merchants with optional filters."""
        df = self._load_csv("merchants")
        
        if df.empty:
            return {"type": "merchant_list", "items": []}
        
        # Apply filters
        if category and "category" in df.columns:
            df = df[df["category"].str.lower() == category.lower()]
        
        # Limit and format
        df = df.head(limit)
        items = df.to_dict("records")
        
        return {
            "type": "merchant_list",
            "count": len(items),
            "filters": {"category": category} if category else {},
            "items": items
        }
    
    def _list_orders(self, status: str = None, category: str = None, time_period: str = None, limit: int = 20) -> Dict[str, Any]:
        """List orders with optional filters."""
        df = self._load_csv("orders")
        
        if df.empty:
            return {"type": "order_list", "items": []}
        
        # Apply filters
        filters = {}
        if status and "status" in df.columns:
            df = df[df["status"].str.lower() == status.lower()]
            filters["status"] = status
            
        if time_period and "order_date" in df.columns:
            try:
                # Handle "Month Year" format e.g. "January 2026"
                parts = time_period.split()
                if len(parts) >= 2:
                    month_str = parts[0]
                    year_str = parts[1]
                    month_map = {
                        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
                        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12
                    }
                    if month_str.lower() in month_map:
                         month_num = month_map[month_str.lower()]
                         df["temp_date"] = pd.to_datetime(df["order_date"])
                         df = df[
                             (df["temp_date"].dt.month == month_num) & 
                             (df["temp_date"].dt.year == int(year_str))
                         ]
                         filters["month"] = time_period
            except Exception as e:
                print(f"Date filter error: {e}")
        
        # Limit and format
        df = df.head(limit)
        items = df.to_dict("records")
        
        return {
            "type": "order_list",
            "count": len(items),
            "filters": filters,
            "items": items
        }
    
    def _list_installments(self, status: str = None, limit: int = 20) -> Dict[str, Any]:
        """List installments with optional filters."""
        df = self._load_csv("installments")
        
        if df.empty:
            return {"type": "installment_list", "items": []}
        
        if status and "status" in df.columns:
            df = df[df["status"].str.lower() == status.lower()]
        
        df = df.head(limit)
        items = df.to_dict("records")
        
        return {
            "type": "installment_list",
            "count": len(items),
            "filters": {"status": status} if status else {},
            "items": items
        }
    
    def _get_category_breakdown(self) -> Dict[str, Any]:
        """Get order breakdown by category."""
        orders = self._load_csv("orders")
        merchants = self._load_csv("merchants")
        
        if orders.empty or merchants.empty:
            return {"type": "category_breakdown", "items": []}
        
        # Merge to get category
        merged = orders.merge(merchants[["merchant_id", "category"]], on="merchant_id", how="left")
        
        # Group by category
        approved = merged[merged["status"] == "approved"]
        breakdown = approved.groupby("category").agg({
            "order_id": "count",
            "amount": "sum"
        }).reset_index()
        breakdown.columns = ["category", "order_count", "gmv"]
        breakdown["gmv"] = breakdown["gmv"].round(2)
        
        return {
            "type": "category_breakdown",
            "items": breakdown.to_dict("records")
        }
    
    def _get_city_breakdown(self) -> Dict[str, Any]:
        """Get order breakdown by city."""
        df = self._load_csv("users")
        
        if df.empty or "city" not in df.columns:
            return {"type": "city_breakdown", "items": []}
        
        breakdown = df["city"].value_counts().reset_index()
        breakdown.columns = ["city", "user_count"]
        
        return {
            "type": "city_breakdown",
            "items": breakdown.to_dict("records")
        }
