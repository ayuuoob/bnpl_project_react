"""
Local Data Adapter - Query the CSV files in /data/silver/ directly.

This adapter allows the agent to work with local CSV data
without needing an external MCP server or database.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd


class LocalDataAdapter:
    """
    Adapter for querying local CSV files.
    
    Provides a pandas-based interface for SQL-like queries
    on the BNPL Silver layer CSV files.
    """
    
    def __init__(self, data_path: Optional[str] = None):
        # Find data path
        if data_path:
            self.data_path = Path(data_path)
        else:
            # Default: look for ../data/silver relative to agents/
            self.data_path = Path(__file__).parent.parent.parent.parent / "data" / "silver"
        
        self._dataframes: Dict[str, pd.DataFrame] = {}
        self._load_data()
    
    def _load_data(self):
        """Load all CSV files into memory."""
        if not self.data_path.exists():
            print(f"Warning: Data path not found: {self.data_path}")
            return
        
        csv_files = list(self.data_path.glob("*.csv"))
        
        for csv_file in csv_files:
            table_name = csv_file.stem  # filename without extension
            try:
                df = pd.read_csv(csv_file)
                self._dataframes[table_name] = df
                print(f"Loaded: {table_name} ({len(df)} rows)")
            except Exception as e:
                print(f"Error loading {csv_file}: {e}")
                
        # --- Batch Score Users for SQL Queries ---
        if "users" in self._dataframes:
            try:
                self._enrich_users_with_scores()
            except Exception as e:
                print(f"Error enriching users with scores: {e}")

    def _enrich_users_with_scores(self):
        """Calculate and attach ML trust scores to users table."""
        try:
            from .ml_tool import _load_uc2_model, _score_and_decide
            from datetime import datetime
            
            artifact = _load_uc2_model()
            if artifact is None:
                return
            
            model = artifact["model"]
            features_list = artifact["features"]
            
            users = self._dataframes.get("users")
            orders = self._dataframes.get("orders")
            installments = self._dataframes.get("installments")
            disputes = self._dataframes.get("disputes")
            
            if users is None:
                return

            # Vectorized feature calculation would be better, but loop is safer for complex logic
            # For hackathon/demo scale (small data), iteration is acceptable
            
            scores = []
            decisions = []
            
            # Pre-calculate aggregates for speed
            order_stats = {}
            if orders is not None:
                order_stats = orders.groupby("user_id").agg({
                    "order_id": "count",
                    "amount": "sum"
                }).to_dict(orient="index")
            
            inst_stats = {}
            if installments is not None:
                # Group by user, then count status
                def calc_rates(x):
                    closed = (x["status"] != "due").sum()
                    late = (x["status"] == "late").sum()
                    active = (x["status"] == "due").sum()
                    late_rate = late / closed if closed > 0 else 0.0
                    return pd.Series([late_rate, active], index=["late_rate", "active"])
                
                inst_stats = installments.groupby("user_id").apply(calc_rates).to_dict(orient="index")

            dispute_stats = {}
            if disputes is not None:
                dispute_stats = disputes.groupby("user_id").size().to_dict()

            rows_to_predict = []
            
            for _, row in users.iterrows():
                uid = row.get("user_id")
                
                # Features
                acc_age = 30
                if "created_at" in row:
                    try:
                        acc_age = (datetime.now() - pd.to_datetime(row["created_at"])).days
                    except: pass
                
                kyc = 1
                try: kyc = int(row.get("kyc_level", 1)) 
                except: pass
                
                # Aggregates
                u_orders = order_stats.get(uid, {})
                orders_30d = u_orders.get("order_id", 0)
                amount_30d = u_orders.get("amount", 0)
                
                u_inst = inst_stats.get(uid, {})
                late_rate = u_inst.get("late_rate", 0.0)
                active_plans = int(u_inst.get("active", 0))
                ontime_rate = 1.0 - late_rate
                
                disputes_90d = dispute_stats.get(uid, 0)
                
                feat_dict = {
                    "account_age_days": acc_age,
                    "kyc_level_num": kyc,
                    "account_status_num": 1,
                    "late_rate_90d": late_rate,
                    "ontime_rate_90d": ontime_rate,
                    "active_plans": active_plans,
                    "orders_30d": orders_30d,
                    "amount_30d": amount_30d,
                    "disputes_90d": disputes_90d,
                    "refunds_90d": 0,
                    "checkout_abandon_rate_30d": 0.0
                }
                rows_to_predict.append(feat_dict)
            
            if not rows_to_predict:
                return

            # Batch Predict
            X = pd.DataFrame(rows_to_predict)
            # Ensure columns
            for f in features_list:
                if f not in X.columns: X[f] = 0
            branch_X = X[features_list]
            
            # Predict
            # _score_and_decide returns (risk_proba, trust_score, decision)
            # But it might not be vectorized in the tool depending on implementation.
            # Let's call model.predict_proba directly for batch speed if possible, 
            # or loop if safe. The ML tool helper is likely scalar.
            # Accessing model directly:
            probs = model.predict_proba(branch_X)[:, 1] # Probability of Class 1 (Risk)
            
            # Add to users DataFrame
            self._dataframes["users"]["risk_probability"] = probs
            self._dataframes["users"]["trust_score"] = ((1 - probs) * 100).astype(int)
            self._dataframes["users"]["risk_score"] = ((1 - probs) * 100).astype(int) # Alias for "User risk score" requests
            
            print(f"Enriched users table with ML scores. Avg Trust Score: {self._dataframes['users']['trust_score'].mean():.1f}")
            
        except Exception as e:
            print(f"Batch scoring failed: {e}")
    
    @property
    def tables(self) -> List[str]:
        """Get list of available tables."""
        return list(self._dataframes.keys())
    
    def get_table(self, table_name: str) -> Optional[pd.DataFrame]:
        """Get a table by name."""
        return self._dataframes.get(table_name)
    
    def get_schema(self) -> Dict[str, List[str]]:
        """Get schema (table names and columns)."""
        schema = {}
        for name, df in self._dataframes.items():
            schema[name] = list(df.columns)
        return schema
    
    def query(self, table_name: str, **kwargs) -> pd.DataFrame:
        """
        Query a table with filters.
        
        Args:
            table_name: Name of the table
            **kwargs: Column filters (e.g., status='approved')
            
        Returns:
            Filtered DataFrame
        """
        df = self.get_table(table_name)
        if df is None:
            return pd.DataFrame()
        
        result = df.copy()
        
        for column, value in kwargs.items():
            if column in result.columns:
                result = result[result[column] == value]
        
        return result
    
    # ==================
    # KPI Calculations
    # ==================
    
    def calculate_gmv(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Calculate GMV (Gross Merchandise Value)."""
        orders = self.get_table("orders")
        if orders is None:
            return {"value": 0, "error": "Orders table not found"}
        
        # Filter by status
        approved = orders[orders["status"] == "approved"] if "status" in orders.columns else orders
        
        # Filter by date if available
        if start_date and "created_at" in approved.columns:
            approved = approved[approved["created_at"] >= start_date]
        if end_date and "created_at" in approved.columns:
            approved = approved[approved["created_at"] <= end_date]
        
        gmv = approved["amount"].sum() if "amount" in approved.columns else 0
        
        return {
            "value": float(gmv),
            "order_count": len(approved),
        }
    
    def calculate_approval_rate(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Calculate approval rate."""
        orders = self.get_table("orders")
        if orders is None:
            return {"value": 0, "error": "Orders table not found"}
        
        # Filter by date if available
        if start_date and "created_at" in orders.columns:
            orders = orders[orders["created_at"] >= start_date]
        if end_date and "created_at" in orders.columns:
            orders = orders[orders["created_at"] <= end_date]
        
        total = len(orders)
        approved = len(orders[orders["status"] == "approved"]) if "status" in orders.columns else 0
        
        rate = approved / total if total > 0 else 0
        
        return {
            "value": float(rate),
            "approved": approved,
            "total": total,
        }
    
    def calculate_late_rate(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Calculate late payment rate."""
        installments = self.get_table("installments")
        if installments is None:
            return {"value": 0, "error": "Installments table not found"}
        
        # Filter by date if available
        if start_date and "due_date" in installments.columns:
            installments = installments[installments["due_date"] >= start_date]
        if end_date and "due_date" in installments.columns:
            installments = installments[installments["due_date"] <= end_date]
        
        total = len(installments)
        late = len(installments[installments["status"] == "late"]) if "status" in installments.columns else 0
        
        rate = late / total if total > 0 else 0
        
        return {
            "value": float(rate),
            "late": late,
            "total": total,
        }
    
    def calculate_active_users(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        """Calculate active users."""
        orders = self.get_table("orders")
        if orders is None:
            return {"value": 0, "error": "Orders table not found"}
        
        # Filter by date if available
        if start_date and "created_at" in orders.columns:
            orders = orders[orders["created_at"] >= start_date]
        if end_date and "created_at" in orders.columns:
            orders = orders[orders["created_at"] <= end_date]
        
        active = orders["user_id"].nunique() if "user_id" in orders.columns else 0
        
        return {
            "value": int(active),
        }
    
    def get_top_merchants(self, metric: str = "gmv", limit: int = 10) -> pd.DataFrame:
        """Get top merchants by metric."""
        orders = self.get_table("orders")
        merchants = self.get_table("merchants")
        
        if orders is None:
            return pd.DataFrame()
        
        if metric == "gmv":
            approved = orders[orders["status"] == "approved"] if "status" in orders.columns else orders
            result = approved.groupby("merchant_id").agg({
                "amount": "sum",
                "order_id": "count"
            }).reset_index()
            result.columns = ["merchant_id", "gmv", "order_count"]
            result = result.sort_values("gmv", ascending=False).head(limit)
        else:
            result = orders.groupby("merchant_id").size().reset_index(name="count")
            result = result.sort_values("count", ascending=False).head(limit)
        
        # Join with merchant names if available
        if merchants is not None and "merchant_name" in merchants.columns:
            result = result.merge(
                merchants[["merchant_id", "merchant_name"]], 
                on="merchant_id", 
                how="left"
            )
        
        return result
    
    def get_delinquency_buckets(self) -> pd.DataFrame:
        """Get delinquency bucket distribution."""
        installments = self.get_table("installments")
        if installments is None or "late_days" not in installments.columns:
            return pd.DataFrame()
        
        late = installments[installments["status"] == "late"] if "status" in installments.columns else installments
        
        def bucket(days):
            if pd.isna(days) or days <= 0:
                return "Not Late"
            elif days <= 7:
                return "1-7 days"
            elif days <= 30:
                return "8-30 days"
            elif days <= 60:
                return "31-60 days"
            else:
                return "60+ days"
        
        late["bucket"] = late["late_days"].apply(bucket)
        result = late.groupby("bucket").size().reset_index(name="count")
        
        # Order buckets
        bucket_order = ["1-7 days", "8-30 days", "31-60 days", "60+ days"]
        result["order"] = result["bucket"].apply(lambda x: bucket_order.index(x) if x in bucket_order else 99)
        result = result.sort_values("order").drop(columns=["order"])
        
        return result


# Singleton instance
_local_data: Optional[LocalDataAdapter] = None


def get_local_data() -> LocalDataAdapter:
    """Get the singleton local data adapter."""
    global _local_data
    if _local_data is None:
        data_path = os.getenv("DATA_PATH")
        _local_data = LocalDataAdapter(data_path)
    return _local_data
