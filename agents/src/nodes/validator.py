import pandas as pd
from typing import Any, Dict, List, Optional
from ..state import AgentState

class ValidatorNode:
    """
    Validator Node (The "Safety Net").
    
    Responsibilities:
    1. Check if data was retrieved successfully.
    2. Summarize list data to prevent raw dumps (LLM Token Limit Protection).
    3. Format fallback messages if AI fails.
    """
    
    def validate_and_summarize(self, data: Any) -> str:
        """Summarize data for LLM to prevent raw dumps."""
        if not data:
            return "No data found."
            
        data_type = data.get("type", "")
        
        # Lists (Orders, Merchants, Users)
        if data_type.endswith("_list"):
            count = data.get("count", 0)
            items = data.get("items", [])
            filters = data.get("filters", {})
            
            if count == 0:
                return f"No items found matching filters: {filters}."
            
            # Summarize items instead of listing them
            summary = [f"Found {count} items. Full table is displayed in the UI."]
            
            if items:
                # Calculate some stats for the LLM to use
                try:
                    df = pd.DataFrame(items)
                    if "amount" in df.columns:
                        total_amount = df["amount"].sum()
                        summary.append(f"Total Amount: {total_amount:,.0f} MAD")
                        avg_amount = df["amount"].mean()
                        summary.append(f"Average Amount: {avg_amount:,.0f} MAD")
                    
                    if "status" in df.columns:
                        status_counts = df["status"].value_counts().to_dict()
                        summary.append(f"Status Breakdown: {status_counts}")
                        
                    if "risk_score" in df.columns:
                        avg_risk = df["risk_score"].mean()
                        summary.append(f"Average Risk Score: {avg_risk:.1f}%")
                except Exception as e:
                    print(f"Summarization error: {e}")
            
            summary.append("INSTRUCTION: Do NOT list individual items. The user sees the table. Provide insights on the stats above.")
            return "\n".join(summary)

        # Risk Overview
        if data_type == "risk_overview":
             return (f"Risk Overview: {data.get('high_risk_count')} high risk installments out of {data.get('total_installments')} total. "
                     f"High risk percentage: {data.get('high_risk_pct')}%. Average Risk Score: {data.get('avg_risk_score')}%.")

        # Top Risky
        if data_type == "top_risky":
            return "Top risky installments provided. Use this to highlight the riskiest users and probability scores. Do not list all."

        # KPI
        if data_type == "kpi_overview":
             metrics = data.get("metrics", {})
             return f"KPIs: GMV={metrics.get('gmv', {}).get('value')}, Approval Rate={metrics.get('approval_rate', {}).get('formatted')}, Late Rate={metrics.get('late_rate', {}).get('formatted')}."
        
        # User/Installment Risk
        if data_type in ["user_risk", "installment_risk"]:
             return f"Risk Analysis for {data.get('user_id') or data.get('installment_id')}: Probability={data.get('proba_late')}%. Explanation: {data.get('explanation')}"

        # Default: truncate string
        return str(data)[:1000]

    def format_fallback(self, state: AgentState, error: str = None) -> str:
        """Simple fallback formatting without LLM - now in natural language."""
        data = state.data
        
        # Check if this was purely an explanation request
        q_lower = state.user_query.lower()
        is_explanation_request = any(x in q_lower for x in ["what is", "what does", "meaning of", "explain"])
        
        if not data:
            if is_explanation_request:
                return (
                    "I don't have specific data for that yet, but I can explain the concept. "
                    "However, if you'd like to see actual numbers, please ask me to show the data."
                )
            
            msg = "I couldn't find any data for your query. Please check your filters."
            if error:
                 msg += f" (System Note: AI Generation failed: {error})"
            return msg
        
        data_type = data.get("type", "")
        
        # KPI Overview
        if data_type == "kpi_overview":
            metrics = data.get("metrics", {})
            gmv = metrics.get("gmv", {}).get("value", 0)
            approval = metrics.get("approval_rate", {}).get("formatted", "0%")
            late = metrics.get("late_rate", {}).get("formatted", "0%")
            orders = metrics.get("orders", {}).get("value", 0)
            
            return (
                f"Currently, the total GMV sits at {gmv:,.2f} MAD with an approval rate of {approval}. "
                f"I'm also seeing a late payment rate of {late} across {orders:,} total orders. "
                f"The donut chart below shows the full order status distribution."
            )
        
        # General Metric
        if "metric" in data and "value" in data:
            metric = data["metric"]
            val = data["value"]
            desc = data.get("description", "")
            currency = data.get("currency", "")
            suffix = f" {currency}" if currency else ""
            
            return f"The total {metric} is {val:,.0f}{suffix}. {desc}"
        
        # Risk Overview
        if data_type == "risk_overview":
            risky = data.get("high_risk_count", 0)
            total = data.get("total_installments", 0)
            avg_score = data.get("avg_risk_score", 0)
            pct = data.get("high_risk_pct", 0)
            
            return (
                f"Our ML model predicts that {risky} out of {total} installments (that's {pct}%) are at high risk of late payment. "
                f"The average risk score across the portfolio is {avg_score}%. "
                f"These are model predictions based on behavioral patterns, not guarantees. "
                f"You can check the donut chart for a visual breakdown of the risk distribution."
            )
        
        # Top Risky
        if data_type == "top_risky":
            items = data.get("items", [])[:5]
            top_user = items[0]['user_id'] if items else "none"
            top_prob = items[0]['proba_late'] if items else 0
            
            return (
                f"Our ML model identifies these installments as having the highest probability of late payment. "
                f"For example, User {top_user} shows a {top_prob}% predicted risk. "
                f"These predictions are based on payment history, account age, and behavior patterns. "
                f"I'd recommend reviewing the bar chart to compare risk probabilities by user."
            )
        
        # Risk Factors
        if data_type == "risk_factors":
            factors = data.get("factors", [])
            top_factors = ", ".join([f"{f['description'].lower()}" for f in factors[:3]])
            
            return (
                f"Our ML model has identified {top_factors} as the most common indicators of potential late payment. "
                f"These are behavioral patterns the model learned from historical data. "
                f"The horizontal bar chart breaks down the frequency of each risk factor."
            )
        
        # User/Installment Risk
        if data_type in ["user_risk", "installment_risk"]:
            if "error" in data:
                return f"I ran into an issue: {data['error']}"
            
            if data_type == "user_risk":
                user_id = data.get('user_id')
                risky = data.get('risky_installments', 0)
                total = data.get('total_installments', 0)
                avg = data.get('avg_risk_score', 0)
                
                return (
                    f"For user {user_id}, our model predicts {risky} out of {total} installments are at risk. "
                    f"The average predicted risk across their plans is {avg}%. "
                    f"You can see the specific reasons and due dates in the detailed table below."
                )
            else:
                inst_id = data.get('installment_id')
                proba = data.get('proba_late', 0)
                user = data.get('user_id')
                reasons = data.get("explanation", {}).get("reason_codes", [])
                reasons_str = "due to " + ", ".join(reasons).lower() if reasons else ""
                
                return (
                    f"For installment {inst_id} (User {user}), the model predicts a {proba}% probability of late payment, {reasons_str}. "
                    f"You can see the contributing factors and full breakdown in the details below."
                )
        
        # Lists
        if data_type.endswith("_list"):
            count = data.get("count", 0)
            entity = data_type.replace("_list", "").replace("_", " ")
            
            return (
                f"I found {count} {entity}s matching your request. "
                f"I've retrieved the full dataset for you - please refer to the detailed table below for the complete list."
            )
        
        # Generic
        return "I've retrieved the data summary you requested. You can see the full details in the table below."
