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
        """Simple fallback formatting without LLM."""
        data = state.data
        
        # Check if this was purely an explanation request
        q_lower = state.user_query.lower()
        is_explanation_request = any(x in q_lower for x in ["what is", "what does", "meaning of", "explain"])
        
        if not data:
            if is_explanation_request:
                return (
                    "🤔 **Explanation Request**\n\n"
                    "I don't have specific data for that yet, but I can explain the concept.\n\n"
                    "Please ask me to *show* the data if you want to see numbers."
                )
            
            msg = "No data found for your query. Please check your filters."
            if error:
                 msg += f"\n\n*(System Note: AI Generation failed: {error})*"
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
                f"📊 **Business KPI Overview**\n\n"
                f"| Metric | Value |\n|--------|-------|\n"
                f"| 💰 GMV | {gmv:,.2f} MAD |\n"
                f"| ✅ Approval Rate | {approval} |\n"
                f"| ⏰ Late Rate | {late} |\n"
                f"| 📦 Total Orders | {orders:,} |\n\n"
                f"📈 **Recommended Chart**: Donut chart to show order status distribution"
            )
        
        # General Metric (e.g. Total GMV alone)
        if "metric" in data and "value" in data:
            metric = data["metric"]
            val = data["value"]
            desc = data.get("description", "")
            currency = data.get("currency", "")
            suffix = f" {currency}" if currency else ""
            
            return (
                f"📊 **{metric}**\n\n"
                f"The total {metric} is **{val:,.0f}{suffix}**.\n"
                f"{desc}\n\n"
                f"💡 **Insight**: Value retrieved directly from database."
            )
        
        # Risk Overview
        if data_type == "risk_overview":
            risky = data.get("high_risk_count", 0)
            total = data.get("total_installments", 0)
            avg_score = data.get("avg_risk_score", 0)
            pct = data.get("high_risk_pct", 0)
            return (
                f"⚠️ **Risk Prediction Overview**\n\n"
                f"Our ML model **predicts** that **{risky}** out of {total} installments ({pct}%) are at high risk of late payment.\n\n"
                f"| Metric | Value |\n|--------|-------|\n"
                f"| 🎯 Total Installments | {total} |\n"
                f"| ⚠️ Predicted High Risk | {risky} |\n"
                f"| 📊 Avg Risk Score | {avg_score}% |\n\n"
                f"💡 **Insight**: These are model predictions based on behavioral patterns, not guarantees.\n\n"
                f"📈 **Recommended Chart**: Donut chart showing risk distribution"
            )
        
        # Top Risky
        if data_type == "top_risky":
            items = data.get("items", [])[:10]
            lines = [
                "📊 **Top Predicted Risky Installments**\n",
                "Our ML model **predicts** these installments have the highest probability of late payment:\n",
                "| User | Installment | Predicted Risk | Due Date |",
                "|------|-------------|----------------|----------|"
            ]
            for item in items:
                lines.append(f"| {item['user_id']} | {item['installment_id']} | {item['proba_late']}% | {item['due_date']} |")
            
            lines.append("\n💡 **Insight**: Risk scores are ML predictions based on payment history, account age, and behavior patterns.")
            lines.append("\n📈 **Recommended Chart**: Bar chart showing risk probability by user")
            return "\n".join(lines)
        
        # Risk Factors
        if data_type == "risk_factors":
            factors = data.get("factors", [])
            lines = [
                "🔍 **Common Risk Factors (Model Insights)**\n",
                "Our ML model identifies these patterns as indicators of potential late payment:\n",
                "| Risk Factor | Description | Occurrences |",
                "|-------------|-------------|-------------|"
            ]
            for f in factors[:7]:
                lines.append(f"| {f['code']} | {f['description']} | {f['occurrences']} |")
            
            lines.append("\n💡 **Insight**: These are behavioral patterns the model learned from historical data.")
            lines.append("\n📈 **Recommended Chart**: Horizontal bar chart of factor frequency")
            return "\n".join(lines)
        
        # User/Installment Risk
        if data_type in ["user_risk", "installment_risk"]:
            if "error" in data:
                return f"⚠️ {data['error']}"
            
            if data_type == "user_risk":
                user_id = data.get('user_id')
                risky = data.get('risky_installments', 0)
                total = data.get('total_installments', 0)
                avg = data.get('avg_risk_score', 0)
                installments = data.get('installments', [])
                
                lines = [
                    f"👤 **User Risk Prediction: {user_id}**\n",
                    f"Our ML model **predicts** {risky} out of {total} installments are at risk of late payment.\n",
                    f"| Metric | Value |\n|--------|-------|\n",
                    f"| 📊 Avg Predicted Risk | {avg}% |\n",
                    f"| ⚠️ High Risk Count | {risky} |\n\n",
                ]
                
                if installments:
                    lines.append("**Installment Details:**\n")
                    lines.append("| Installment | Risk | Due Date | Reasons |")
                    lines.append("|-------------|------|----------|---------|")
                    for inst in installments[:5]:
                        reasons = ", ".join(inst.get("reason_codes", []))[:30] or "—"
                        lines.append(f"| {inst['installment_id']} | {inst['proba_late']}% | {inst['due_date']} | {reasons} |")
                
                return "\n".join(lines)
            else:
                inst_id = data.get('installment_id')
                proba = data.get('proba_late', 0)
                reasons = data.get("explanation", {}).get("reason_codes", [])
                reasons_str = ", ".join(reasons) if reasons else "No specific patterns"
                factors = data.get("explanation", {}).get("top_factors", [])
                
                lines = [
                    f"📄 **Installment Risk Prediction: {inst_id}**\n",
                    f"Our ML model **predicts** a **{proba}%** probability of late payment.\n",
                    f"| Field | Value |\n|-------|-------|\n",
                    f"| User | {data.get('user_id')} |\n",
                    f"| Due Date | {data.get('due_date')} |\n",
                    f"| Risk Patterns | {reasons_str} |\n\n",
                ]
                
                if factors:
                    lines.append("**Top Contributing Factors:**\n")
                    for f in factors[:3]:
                        direction = "↑ increases" if f['direction'] == 'increases_risk' else "↓ decreases"
                        lines.append(f"- `{f['feature']}` {direction} risk")
                
                return "\n".join(lines)
        
        # Lists
        if data_type.endswith("_list"):
            count = data.get("count", 0)
            items = data.get("items", [])
            entity = data_type.replace("_list", "").title()
            
            summary =  f"📋 **{entity}s** ({count} found)\n\n"
            summary += "I have retrieved the data requested. Please refer to the **detailed table below** for the full list.\n\n"
            
            if error:
                summary += f"*(System Note: AI Insights unavailable: {error})*"
            else:
                summary += "💡 **Insight**: Data loaded successfully."
                
            return summary
        
        # Generic
        return f"📊 Data Summary:\nTable displayed below.\n\n💡 **Insight**: Value retrieved directly from database." + (f"\n*(Debug: {error})*" if error else "")
