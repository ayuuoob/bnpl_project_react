"""
Risk Handler - Risk Analysis and Explanations

Handles queries about risk scores, late payment predictions, and explanations.
Uses pre-scored data from uc1_scored_today.csv and explanations from JSONL.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..state import AgentState


class RiskHandler:
    """Handler for risk analysis queries."""
    
    def __init__(self, data_path: str = "../data"):
        self.data_path = Path(data_path)
        self._scored_df = None
        self._explanations = None
    
    @property
    def scored_df(self) -> pd.DataFrame:
        """Lazy load scored installments data."""
        if self._scored_df is None:
            path = self.data_path / "gold" / "uc1_scored_today.csv"
            if path.exists():
                self._scored_df = pd.read_csv(path)
            else:
                self._scored_df = pd.DataFrame()
        return self._scored_df
    
    @property
    def explanations(self) -> Dict[str, dict]:
        """Lazy load explanations indexed by installment_id."""
        if self._explanations is None:
            self._explanations = {}
            path = self.data_path / "scoring" / "uc1_explanations_today.jsonl"
            if path.exists():
                with open(path, "r") as f:
                    for line in f:
                        if line.strip():
                            record = json.loads(line)
                            inst_id = record.get("context", {}).get("ids", {}).get("installment_id")
                            if inst_id:
                                self._explanations[inst_id] = record
        return self._explanations
    
    async def handle(self, state: AgentState) -> AgentState:
        """Handle risk query and populate state with data."""
        query_lower = state.user_query.lower()
        entities = state.entities
        
        try:
            # ===== HIGHEST RISK / POTENTIAL FRAUD USERS =====
            # "user with highest risk", "highest risk user", "most risky user"
            # "who could fraud", "potential fraud", "can't trust", "untrusted users"
            if any(phrase in query_lower for phrase in [
                "highest risk", "most risk", "riskiest", 
                "highest score", "top risk",
                "could fraud", "will fraud", "potential fraud",
                "can't trust", "cannot trust", "don't trust", "untrust",
                "might late", "will be late", "predict late"
            ]):
                limit = entities.limit or 10
                state.data = self._get_highest_risk_users(limit)
            
            # ===== PER-USER RISK SCORES (all users) =====
            # "risk score for all users", "each user risk", "user risk scores"
            elif any(phrase in query_lower for phrase in [
                "each user", "all user", "every user",
                "user risk score", "risk score for user",
                "score of user", "scores of user"
            ]) or ("risk score" in query_lower and "user" in query_lower and not entities.user_id):
                limit = entities.limit or 20
                state.data = self._get_all_user_risk_scores(limit)
            
            # ===== TRUST SCORE (UC2) =====
            elif "trust" in query_lower or ("score" in query_lower and "risk" not in query_lower):
                if entities.user_id:
                    state.data = self._get_trust_score(entities.user_id)
                else:
                    state.data = self._get_trust_score_demo()
            
            # ===== SPECIFIC LOOKUPS =====
            elif entities.installment_id:
                state.data = self._get_installment_risk(entities.installment_id)
            
            elif entities.user_id:
                state.data = self._get_user_risk(entities.user_id)
            
            # ===== RISK OVERVIEW =====
            elif "overview" in query_lower or "summary" in query_lower:
                state.data = self._get_risk_overview()
            
            # ===== TOP RISKY INSTALLMENTS =====
            elif "top" in query_lower or "risky" in query_lower:
                limit = entities.limit or 10
                state.data = self._get_top_risky(limit)
            
            # ===== RISK FACTORS =====
            elif "factor" in query_lower or "reason" in query_lower or "why" in query_lower:
                state.data = self._get_risk_factors()
            
            # ===== DISTRIBUTION =====
            elif "distribution" in query_lower:
                state.data = self._get_risk_distribution()
            
            # ===== DEFAULT: show user risk scores (more useful than overview) =====
            else:
                state.data = self._get_all_user_risk_scores(20)
                
        except Exception as e:
            state.error = f"Error analyzing risk: {str(e)}"
        
        return state
    
    def _get_highest_risk_users(self, limit: int = 10) -> Dict[str, Any]:
        """Get users with highest predicted risk (potential fraud/late payment)."""
        df = self.scored_df
        if df.empty or "user_id" not in df.columns:
            return {"type": "high_risk_users", "error": "No user data available", "items": []}
        
        # Aggregate risk by user - find users with highest average risk
        user_risk = df.groupby("user_id").agg({
            "proba_late_30d": "max",  # Max risk for identifying highest risk
            "is_risky_late": "sum",
            "installment_id": "count"
        }).reset_index()
        
        user_risk.columns = ["user_id", "max_risk_proba", "risky_count", "total_installments"]
        
        # Calculate risk score percentage
        user_risk["risk_score"] = (user_risk["max_risk_proba"] * 100).round(1)
        
        # Sort by highest risk first
        user_risk = user_risk.sort_values("risk_score", ascending=False).head(limit)
        
        # Build items with fraud/risk prediction labels
        items = []
        for _, row in user_risk.iterrows():
            risk_level = "🔴 HIGH FRAUD RISK" if row["risk_score"] >= 50 else (
                "🟡 MEDIUM RISK" if row["risk_score"] >= 30 else "🟢 LOW RISK"
            )
            items.append({
                "user_id": row["user_id"],
                "risk_score": row["risk_score"],
                "risk_level": risk_level,
                "prediction": f"Model predicts {row['risk_score']}% chance of late payment",
                "risky_installments": int(row["risky_count"]),
                "total_installments": int(row["total_installments"])
            })
        
        # Get the highest risk user for highlight
        top_user = items[0] if items else {}
        
        return {
            "type": "high_risk_users",
            "count": len(items),
            "items": items,
            "highlight": {
                "user_id": top_user.get("user_id", "N/A"),
                "risk_score": top_user.get("risk_score", 0),
                "message": f"⚠️ {top_user.get('user_id', 'N/A')} has the HIGHEST predicted fraud risk at {top_user.get('risk_score', 0)}%"
            },
            "summary": {
                "high_fraud_risk_count": len([i for i in items if i["risk_score"] >= 50]),
                "medium_risk_count": len([i for i in items if 30 <= i["risk_score"] < 50]),
                "avg_risk_score": round(sum(i["risk_score"] for i in items) / len(items), 1) if items else 0
            },
            # Bar chart - sorted by risk
            "chart_data": {
                "type": "bar",
                "title": "🔴 Highest Fraud Risk Users (ML Prediction)",
                "x_label": "User",
                "y_label": "Predicted Risk %",
                "labels": [item["user_id"] for item in items],
                "values": [item["risk_score"] for item in items],
                "color": "#ff6b6b"
            }
        }
    
    def _get_all_user_risk_scores(self, limit: int = 20) -> Dict[str, Any]:
        """Calculate risk score for each user using ML model predictions."""
        df = self.scored_df
        if df.empty or "user_id" not in df.columns:
            return {"type": "user_risk_list", "error": "No user data available", "items": []}
        
        # Aggregate risk by user
        user_risk = df.groupby("user_id").agg({
            "proba_late_30d": "mean",  # Average risk probability
            "is_risky_late": "sum",     # Count of risky installments
            "installment_id": "count"   # Total installments
        }).reset_index()
        
        user_risk.columns = ["user_id", "avg_risk_proba", "risky_count", "total_installments"]
        
        # Calculate trust score (inverse of risk)
        user_risk["risk_score"] = (user_risk["avg_risk_proba"] * 100).round(1)
        user_risk["trust_score"] = (100 - user_risk["risk_score"]).round(0).astype(int)
        
        # Determine risk category
        def categorize(score):
            if score >= 70:
                return "Low Risk"
            elif score >= 40:
                return "Medium Risk"
            else:
                return "High Risk"
        
        user_risk["risk_category"] = user_risk["trust_score"].apply(categorize)
        
        # Sort by risk (highest first)
        user_risk = user_risk.sort_values("risk_score", ascending=False).head(limit)
        
        # Build items list
        items = []
        for _, row in user_risk.iterrows():
            items.append({
                "user_id": row["user_id"],
                "risk_score": row["risk_score"],
                "trust_score": int(row["trust_score"]),
                "risk_category": row["risk_category"],
                "risky_installments": int(row["risky_count"]),
                "total_installments": int(row["total_installments"])
            })
        
        # Prepare chart data - bar chart of risk scores
        return {
            "type": "user_risk_list",
            "count": len(items),
            "items": items,
            "summary": {
                "total_users": len(user_risk),
                "high_risk_users": len([i for i in items if i["risk_category"] == "High Risk"]),
                "avg_risk_score": round(user_risk["risk_score"].mean(), 1)
            },
            # Bar chart for visualization
            "chart_data": {
                "type": "bar",
                "title": "Predicted Risk Score by User",
                "x_label": "User",
                "y_label": "Risk Score (%)",
                "labels": [item["user_id"] for item in items[:15]],  # Top 15 for chart
                "values": [item["risk_score"] for item in items[:15]],
                "color": "#ff6b6b"
            }
        }
    
    def _get_trust_score(self, user_id: str) -> Dict[str, Any]:
        """Get trust score for a specific user using UC2 model features."""
        df = self.scored_df
        
        # Find user data
        user_rows = df[df["user_id"] == user_id] if "user_id" in df.columns else pd.DataFrame()
        
        if user_rows.empty:
            # Use demo features
            return self._get_trust_score_demo(user_id)
        
        # Build features from available data
        row = user_rows.iloc[0]
        
        # Calculate aggregated features
        late_rate = row.get("proba_late_30d", 0.1)
        risky_count = len(user_rows[user_rows["is_risky_late"] == 1]) if "is_risky_late" in user_rows.columns else 0
        total_count = len(user_rows)
        
        # Trust score calculation (inverse of risk)
        trust_score = max(0, min(100, int((1 - late_rate) * 100)))
        
        # Decision based on threshold
        if trust_score >= 70:
            decision = "APPROVED_3X"
            decision_color = "#51cf66"
        elif trust_score >= 40:
            decision = "APPROVED_WITH_LIMIT"
            decision_color = "#ffc107"
        else:
            decision = "REJECTED_3X"
            decision_color = "#ff6b6b"
        
        # Explanation
        explanations = []
        if late_rate > 0.3:
            explanations.append("High late payment history")
        if risky_count > 2:
            explanations.append("Multiple risky installments")
        if not explanations:
            explanations.append("Good payment behavior")
        
        return {
            "type": "trust_score",
            "user_id": user_id,
            "trust_score": trust_score,
            "risk_probability": round(late_rate * 100, 1),
            "decision": decision,
            "decision_color": decision_color,
            "explanation": " | ".join(explanations),
            "total_installments": total_count,
            "risky_installments": risky_count,
            # Gauge chart for trust score
            "chart_data": {
                "type": "gauge",
                "title": f"Trust Score for {user_id}",
                "value": trust_score,
                "max_value": 100,
                "reference": 70,  # Approval threshold
                "threshold": 40   # Limit threshold
            }
        }
    
    def _get_trust_score_demo(self, user_id: str = "demo_user") -> Dict[str, Any]:
        """Get demo trust score when user not found."""
        # Demo score for demonstration
        trust_score = 72
        
        return {
            "type": "trust_score",
            "user_id": user_id,
            "trust_score": trust_score,
            "risk_probability": 28.0,
            "decision": "APPROVED_3X",
            "decision_color": "#51cf66",
            "explanation": "Good payment behavior | Account age > 60 days",
            "total_installments": 5,
            "risky_installments": 0,
            "demo": True,
            # Gauge chart
            "chart_data": {
                "type": "gauge",
                "title": f"Trust Score (Demo)",
                "value": trust_score,
                "max_value": 100,
                "reference": 70,
                "threshold": 40
            }
        }
    
    def _get_risk_overview(self) -> Dict[str, Any]:
        """Get overall risk statistics."""
        df = self.scored_df
        if df.empty:
            return {"type": "risk_overview", "error": "No scored data available"}
        
        total = len(df)
        risky = len(df[df["is_risky_late"] == 1]) if "is_risky_late" in df.columns else 0
        safe = total - risky
        avg_proba = df["proba_late_30d"].mean() if "proba_late_30d" in df.columns else 0
        
        return {
            "type": "risk_overview",
            "total_installments": total,
            "high_risk_count": risky,
            "low_risk_count": safe,
            "high_risk_pct": round(risky / total * 100, 1) if total > 0 else 0,
            "avg_risk_score": round(avg_proba * 100, 1),
            "risk_threshold": 49.0,
            "explanations_available": len(self.explanations),
            # Chart data for webapp
            "chart_data": {
                "type": "donut",
                "title": "Predicted Risk Distribution",
                "labels": ["High Risk (Model Predicted)", "Low Risk"],
                "values": [risky, safe],
                "colors": ["#ff6b6b", "#51cf66"]
            }
        }
    
    def _get_top_risky(self, limit: int = 10) -> Dict[str, Any]:
        """Get top risky installments."""
        df = self.scored_df
        if df.empty:
            return {"type": "top_risky", "items": []}
        
        # Filter risky and sort by probability
        if "is_risky_late" in df.columns and "proba_late_30d" in df.columns:
            risky = df[df["is_risky_late"] == 1].nlargest(limit, "proba_late_30d")
        else:
            risky = df.head(limit)
        
        items = []
        for _, row in risky.iterrows():
            items.append({
                "installment_id": row.get("installment_id"),
                "user_id": row.get("user_id"),
                "proba_late": round(row.get("proba_late_30d", 0) * 100, 1),
                "due_date": str(row.get("due_date", ""))
            })
        
        return {
            "type": "top_risky",
            "count": len(items),
            "items": items,
            # Chart data for webapp
            "chart_data": {
                "type": "bar",
                "title": "Top Predicted Risky Installments",
                "x_label": "User",
                "y_label": "Predicted Risk %",
                "labels": [item["user_id"] for item in items],
                "values": [item["proba_late"] for item in items],
                "color": "#ff6b6b"
            }
        }
    
    def _get_installment_risk(self, inst_id: str) -> Dict[str, Any]:
        """Get risk details for a specific installment."""
        df = self.scored_df
        
        # Find in scored data
        row = df[df["installment_id"] == inst_id].iloc[0] if inst_id in df["installment_id"].values else None
        
        if row is None:
            return {"type": "installment_risk", "error": f"Installment {inst_id} not found"}
        
        result = {
            "type": "installment_risk",
            "installment_id": inst_id,
            "user_id": row.get("user_id"),
            "order_id": row.get("order_id"),
            "proba_late": round(row.get("proba_late_30d", 0) * 100, 1),
            "is_risky": bool(row.get("is_risky_late", 0)),
            "due_date": str(row.get("due_date", "")),
            "status": row.get("status")
        }
        
        # Add explanation if available
        if inst_id in self.explanations:
            exp = self.explanations[inst_id]
            result["explanation"] = {
                "reason_codes": exp.get("explainability", {}).get("reason_code", []),
                "top_factors": self._format_factors(exp.get("explainability", {}).get("top_factors", [])),
                "recommendation": exp.get("recommendations", {}).get("limit_adjustment", {})
            }
        
        return result
    
    def _get_user_risk(self, user_id: str) -> Dict[str, Any]:
        """Get risk details for all installments of a user."""
        df = self.scored_df
        
        # Filter by user
        user_rows = df[df["user_id"] == user_id] if "user_id" in df.columns else pd.DataFrame()
        
        if user_rows.empty:
            return {"type": "user_risk", "error": f"User {user_id} not found in scored data"}
        
        installments = []
        for _, row in user_rows.iterrows():
            inst = {
                "installment_id": row.get("installment_id"),
                "proba_late": round(row.get("proba_late_30d", 0) * 100, 1),
                "is_risky": bool(row.get("is_risky_late", 0)),
                "due_date": str(row.get("due_date", ""))
            }
            
            # Add explanation if available
            inst_id = row.get("installment_id")
            if inst_id in self.explanations:
                exp = self.explanations[inst_id]
                inst["reason_codes"] = exp.get("explainability", {}).get("reason_code", [])
            
            installments.append(inst)
        
        # Get overall user stats
        risky_count = len([i for i in installments if i["is_risky"]])
        avg_risk = sum(i["proba_late"] for i in installments) / len(installments) if installments else 0
        
        return {
            "type": "user_risk",
            "user_id": user_id,
            "total_installments": len(installments),
            "risky_installments": risky_count,
            "avg_risk_score": round(avg_risk, 1),
            "installments": installments
        }
    
    def _get_risk_factors(self) -> Dict[str, Any]:
        """Get common risk factors from explanations."""
        reason_counts = {}
        
        for exp in self.explanations.values():
            reasons = exp.get("explainability", {}).get("reason_code", [])
            for reason in reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        # Sort by frequency
        sorted_reasons = sorted(reason_counts.items(), key=lambda x: -x[1])
        
        # Reason code descriptions
        descriptions = {
            "HIGH_LOAD": "High number of active payment plans",
            "LOW_KYC": "Incomplete KYC verification",
            "LOW_TRUST_SCORE": "Low user trust score",
            "HIGH_SPEND_PRESSURE": "Spending beyond normal patterns",
            "REPEATED_LATE_PAYMENTS": "History of late payments",
            "POOR_ON_TIME_HISTORY": "Poor on-time payment record",
            "SEVERE_LATE_BEHAVIOR": "Extreme lateness patterns"
        }
        
        factors = []
        for reason, count in sorted_reasons:
            factors.append({
                "code": reason,
                "description": descriptions.get(reason, reason),
                "occurrences": count
            })
        
        return {
            "type": "risk_factors",
            "total_explanations": len(self.explanations),
            "factors": factors,
            # Chart data for webapp
            "chart_data": {
                "type": "bar_horizontal",
                "title": "Risk Factor Frequency (Model Insights)",
                "x_label": "Occurrences",
                "y_label": "Risk Factor",
                "labels": [f["description"][:25] for f in factors],
                "values": [f["occurrences"] for f in factors],
                "color": "#ffa94d"
            }
        }
    
    def _get_risk_distribution(self) -> Dict[str, Any]:
        """Get risk score distribution."""
        df = self.scored_df
        if df.empty or "proba_late_30d" not in df.columns:
            return {"type": "risk_distribution", "buckets": []}
        
        # Create buckets
        buckets = [
            (0, 0.18, "5-18%"),
            (0.18, 0.31, "18-31%"),
            (0.31, 0.44, "31-44%"),
            (0.44, 0.58, "44-58%"),
            (0.58, 0.71, "58-71%")
        ]
        
        distribution = []
        for low, high, label in buckets:
            count = len(df[(df["proba_late_30d"] >= low) & (df["proba_late_30d"] < high)])
            distribution.append({"range": label, "count": count})
        
        return {
            "type": "risk_distribution",
            "buckets": distribution,
            "threshold": 0.49
        }
    
    def _format_factors(self, factors: List[dict]) -> List[dict]:
        """Format top factors for display."""
        formatted = []
        for f in factors[:5]:  # Top 5
            formatted.append({
                "feature": f.get("feature", "").replace("num__", "").replace("cat__", ""),
                "direction": f.get("direction", ""),
                "contribution": round(f.get("contribution_logodds", 0), 3)
            })
        return formatted
