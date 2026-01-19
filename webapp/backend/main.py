"""
FastAPI Backend for BNPL Copilot
Connects React frontend to existing agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Any, Dict, List
import sys
import os
from pathlib import Path
import asyncio

# Add agents path
BACKEND_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = BACKEND_DIR.parent.parent
AGENTS_PATH = PROJECT_ROOT / "agents"

sys.path.insert(0, str(AGENTS_PATH))
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(AGENTS_PATH / ".env")

# Import agent - use async version
from src.graph import run_query_with_chart, get_copilot

app = FastAPI(title="BNPL Copilot API", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== MODELS =====
class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = []
    
class KPI(BaseModel):
    label: str
    value: str
    unit: Optional[str] = None

class ChartSeries(BaseModel):
    dataKey: str
    color: Optional[str] = "#3b82f6"

class ChartData(BaseModel):
    id: str
    kind: str  # 'bar' or 'line'
    title: str
    xKey: str
    series: List[ChartSeries]
    rows: List[Dict[str, Any]]

class TableData(BaseModel):
    id: str
    title: str
    columns: List[str]
    rows: List[Dict[str, Any]]

class CardData(BaseModel):
    title: str
    items: List[str]

class AnalyticsPayload(BaseModel):
    kpis: Optional[List[KPI]] = []
    charts: Optional[List[ChartData]] = []
    tables: Optional[List[TableData]] = []
    cards: Optional[List[CardData]] = []

class ChatResponse(BaseModel):
    id: str
    role: str
    content: str
    hasAnalytics: bool
    analytics: Optional[AnalyticsPayload] = None

import numpy as np

# ===== HELPER FUNCTIONS =====
def convert_numpy(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, dict):
        return {k: convert_numpy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy(i) for i in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return convert_numpy(obj.tolist())
    return obj

def extract_kpis(data: dict) -> List[KPI]:
    """Extract KPIs from agent data."""
    if not data:
        return []
    
    kpis = []
    data_type = data.get("type", "")
    
    # Generic extraction if type is missing or generic
    if not data_type or data_type == "general":
        if "metric" in data and "value" in data:
             kpis.append(KPI(label=data["metric"], value=str(data["value"])))
        for k, v in data.items():
            if isinstance(v, (int, float, str)) and k not in ["type", "text", "response"]:
                if "id" not in k.lower() and len(str(v)) < 20:
                     kpis.append(KPI(label=k.replace("_", " ").title(), value=str(v)))
    
    if data_type == "high_risk_users":
        summary = data.get("summary", {})
        highlight = data.get("highlight", {})
        kpis.append(KPI(label="High Risk Users", value=str(data.get("count", 0))))
        kpis.append(KPI(label="Highest Risk", value=f"{highlight.get('risk_score', 0)}%"))
        kpis.append(KPI(label="Avg Risk Score", value=f"{summary.get('avg_risk_score', 0)}%"))
    
    elif data_type == "risk_overview":
        kpis.append(KPI(label="High Risk Users", value=str(data.get("high_risk_count", 0))))
        kpis.append(KPI(label="Total Installments", value=str(data.get("total_installments", 0))))
        kpis.append(KPI(label="Avg Risk Score", value=f"{data.get('avg_risk_score', 0)}%"))
        kpis.append(KPI(label="Risk Rate", value=f"{data.get('high_risk_pct', 0)}%"))
    
    elif data_type == "user_risk_list":
        summary = data.get("summary", {})
        kpis.append(KPI(label="Users Analyzed", value=str(data.get("count", 0))))
        kpis.append(KPI(label="High Risk", value=str(summary.get("high_risk_users", 0))))
        kpis.append(KPI(label="Avg Risk", value=f"{summary.get('avg_risk_score', 0)}%"))
    
    elif data_type == "trust_score":
        kpis.append(KPI(label="Trust Score", value=str(data.get("trust_score", 0))))
        kpis.append(KPI(label="Decision", value=data.get("decision", "N/A")[:15]))
        kpis.append(KPI(label="Risk %", value=f"{data.get('risk_probability', 0)}%"))
    
    elif data_type == "kpi_overview" or ("gmv" in data and isinstance(data["gmv"], dict)): # Expanded check
        metrics = data.get("metrics", data) # Fallback to data itself if metrics not present
        if "gmv" in metrics:
            val = metrics['gmv'] if isinstance(metrics['gmv'], (int, float, str)) else metrics['gmv'].get('value', 0)
            kpis.append(KPI(label="Total GMV", value=f"{val:,.0f}" if isinstance(val, (int, float)) else str(val), unit="MAD"))
        if "approval_rate" in metrics:
            val = metrics['approval_rate']
            v = val if isinstance(val, (int, float, str)) else val.get('formatted', '0%')
            kpis.append(KPI(label="Approval Rate", value=str(v)))
        if "late_rate" in metrics:
             val = metrics['late_rate']
             v = val if isinstance(val, (int, float, str)) else val.get('formatted', '0%')
             kpis.append(KPI(label="Late Rate", value=str(v)))
        if "total_orders" in metrics or "orders" in metrics:
             val = metrics.get('total_orders', metrics.get('orders'))
             v = val if isinstance(val, (int, float, str)) else val.get('value', 0)
             kpis.append(KPI(label="Total Orders", value=f"{v:,}" if isinstance(v, (int, float)) else str(v)))

    return kpis[:8] # Limit to 8 KPIs


def extract_chart(data: dict, chart_data: dict) -> List[ChartData]:
    """Extract and auto-generate charts from agent data."""
    charts = []

    # 1. Use explicit chart data from agent if available
    if chart_data:
        chart_type = chart_data.get("type", "bar")
        labels = chart_data.get("labels", [])
        values = chart_data.get("values", [])
        title = chart_data.get("title", "Chart")
        
        kind = "bar"
        if chart_type == "line": kind = "line"
        elif chart_type in ["doughnut", "donut"]: kind = "doughnut"
        elif chart_type == "pie": kind = "pie"
        elif chart_type == "area": kind = "area"
        elif chart_type == "scatter": kind = "scatter"
        elif chart_type == "radar": kind = "radar"
        elif chart_type == "funnel": kind = "funnel"
        
        rows = [{"name": str(l), "value": v} for l, v in zip(labels, values)]
        
        charts.append(ChartData(
            id=f"chart_agent_{len(charts)}",
            kind=kind,
            title=title,
            xKey="name",
            series=[ChartSeries(dataKey="value", color=chart_data.get("color", "#667eea"))],
            rows=rows[:30]
        ))

    # 2. Auto-generate charts from raw data items if possible
    items = data.get("items", [])
    if items and isinstance(items, list) and len(items) > 0:
        keys = list(items[0].keys())
        
        # Try to find suitable keys for axes
        date_key = next((k for k in keys if "date" in k.lower() or "day" in k.lower() or "month" in k.lower()), None)
        value_key = next((k for k in keys if isinstance(items[0][k], (int, float)) and "id" not in k.lower()), None)
        category_key = next((k for k in keys if k not in [date_key, value_key] and isinstance(items[0][k], str)), None)

        if value_key:
            # A) Trend Chart (if date exists)
            if date_key:
                # Group by date
                trend_data = {}
                for item in items:
                    d = item.get(date_key)
                    v = item.get(value_key, 0)
                    if d:
                        trend_data[d] = trend_data.get(d, 0) + v
                
                sorted_trend = sorted([{"name": k, "value": v} for k, v in trend_data.items()], key=lambda x: x["name"])
                
                charts.append(ChartData(
                    id=f"chart_auto_trend_{len(charts)}",
                    kind="area",
                    title=f"{value_key.replace('_', ' ').title()} Over Time",
                    xKey="name",
                    series=[ChartSeries(dataKey="value", color="#8884d8")],
                    rows=sorted_trend
                ))

            # B) Distribution Chart (Pie/Donut) - Top 5 Categories
            if category_key:
                cat_data = {}
                for item in items:
                    c = item.get(category_key)
                    v = item.get(value_key, 0)
                    if c:
                        cat_data[c] = cat_data.get(c, 0) + v
                
                sorted_cat = sorted([{"name": k, "value": v} for k, v in cat_data.items()], key=lambda x: x["value"], reverse=True)[:5]
                
                if len(sorted_cat) > 1:
                    charts.append(ChartData(
                        id=f"chart_auto_dist_{len(charts)}",
                        kind="doughnut",
                        title=f"Top 5 {category_key.replace('_', ' ').title()}",
                        xKey="name",
                        series=[ChartSeries(dataKey="value")],
                        rows=sorted_cat
                    ))
                    
                    # Also add a Bar chart for full comparison
                    charts.append(ChartData(
                        id=f"chart_auto_bar_{len(charts)}",
                        kind="bar",
                        title=f"{value_key.replace('_', ' ').title()} by {category_key.replace('_', ' ').title()}",
                        xKey="name",
                        series=[ChartSeries(dataKey="value", color="#82ca9d")],
                        rows=sorted_cat
                    ))

            # C) Risk Distribution (Specific logic)
            if "risk_score" in keys:
                 risk_bins = {"Low": 0, "Medium": 0, "High": 0}
                 for item in items:
                     score = item.get("risk_score", 0)
                     if score < 30: risk_bins["Low"] += 1
                     elif score < 70: risk_bins["Medium"] += 1
                     else: risk_bins["High"] += 1
                 
                 charts.append(ChartData(
                    id=f"chart_auto_risk_{len(charts)}",
                    kind="pie",
                    title="Risk Distribution",
                    xKey="name",
                    series=[ChartSeries(dataKey="value")],
                    rows=[{"name": k, "value": v} for k,v in risk_bins.items() if v > 0]
                 ))
    
    # 3. Handle Generic Metrics (single values)
    if not charts and (data.get("type", "") in ["kpi_overview", "general"] or "metrics" in data):
        metrics = data.get("metrics", data)
        valid_metrics = {k: v for k, v in metrics.items() if isinstance(v, (int, float)) or (isinstance(v, dict) and "value" in v)}
        
        if len(valid_metrics) >= 2:
            rows = []
            for k, v in valid_metrics.items():
                val = v if isinstance(v, (int, float)) else v.get("value", 0)
                if isinstance(val, (int, float)):
                    rows.append({"name": k.replace("_", " ").title(), "value": val})
            
            if rows:
                charts.append(ChartData(
                    id=f"chart_auto_metrics_{len(charts)}",
                    kind="bar",
                    title="Key Metrics Comparison",
                    xKey="name",
                    series=[ChartSeries(dataKey="value", color="#3b82f6")],
                    rows=rows
                ))

    return charts


def extract_table(data: dict) -> Optional[TableData]:
    """Extract table from agent data."""
    if not data or "items" not in data:
        return None
    
    items = data.get("items", [])
    if not items:
        return None
    
    columns = list(items[0].keys()) if items else []
    
    return TableData(
        id="table_1",
        title=data.get("type", "Data").replace("_", " ").title(),
        columns=columns,
        rows=items[:20]  # Limit to 20 rows
    )


# ===== ENDPOINTS =====
@app.get("/")
async def root():
    return {"status": "ok", "message": "BNPL Copilot API"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process chat message and return response with analytics."""
    try:
        # Call agent
        result = await run_query_with_chart(request.message, request.history)
        response_text = result.get("response", "I couldn't process that query.")
        chart_data = result.get("chart_data")
        
        # Get raw data
        copilot = get_copilot()
        raw_data_orig = getattr(copilot, '_last_data', None) or {}
        print(f"DEBUG: raw_data_orig type: {type(raw_data_orig)}")
        print(f"DEBUG: raw_data_orig: {raw_data_orig}")
        
        raw_data = convert_numpy(raw_data_orig)
        print(f"DEBUG: raw_data (converted): {raw_data}")
        
        # Build analytics
        kpis = extract_kpis(raw_data)
        print(f"DEBUG: extracted kpis: {kpis}")
        
        # Smart chart generation (returns a list)
        charts = extract_chart(raw_data, chart_data)
        print(f"DEBUG: extracted charts: {charts}")
        
        tables = []
        table = extract_table(raw_data)
        if table:
            tables.append(table)
        
        analytics = AnalyticsPayload(
            kpis=kpis,
            charts=charts,
            tables=tables,
            cards=[]
        )
        
        has_analytics = bool(kpis or charts or tables)
        print(f"DEBUG: has_analytics: {has_analytics}")
        
        return ChatResponse(
            id=f"msg_{hash(request.message)}",
            role="assistant",
            content=response_text,
            hasAnalytics=has_analytics,
            analytics=analytics if has_analytics else None
        )
        
    except Exception as e:
        return ChatResponse(
            id="error",
            role="assistant",
            content=f"Error processing query: {str(e)}",
            hasAnalytics=False,
            analytics=None
        )


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


# ===== DASHBOARD DATA ENDPOINTS =====
import pandas as pd

DATA_DIR = PROJECT_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"
SILVER_DIR = DATA_DIR / "silver"


@app.get("/api/dashboard/kpis")
async def get_dashboard_kpis():
    """Get KPI metrics for the dashboard from real data."""
    try:
        # Load data
        orders_df = pd.read_csv(SILVER_DIR / "orders.csv")
        users_df = pd.read_csv(SILVER_DIR / "users.csv")
        gold_orders_df = pd.read_csv(GOLD_DIR / "gold_orders_analytics.csv")
        
        # Calculate GMV (sum of approved orders)
        approved_orders = orders_df[orders_df["status"] == "approved"]
        total_gmv = int(approved_orders["amount"].sum())  # Convert to native Python int
        
        # Active users (status = active)
        active_users = int(users_df[users_df["account_status"] == "active"].shape[0])
        
        # Default rate from gold_orders (orders with late installments / total orders with installments)
        orders_with_installments = gold_orders_df[gold_orders_df["installments_count_y"] > 0]
        if len(orders_with_installments) > 0:
            default_orders = orders_with_installments[orders_with_installments["late_installments"] > 0]
            default_rate = float((len(default_orders) / len(orders_with_installments)) * 100)
        else:
            default_rate = 0.0
        
        # Approval rate
        total_orders = len(orders_df)
        approved_count = len(approved_orders)
        approval_rate = float((approved_count / total_orders * 100)) if total_orders > 0 else 0.0
        
        # Format GMV
        if total_gmv >= 1_000_000:
            gmv_formatted = f"MAD {total_gmv / 1_000_000:.1f}M"
        else:
            gmv_formatted = f"MAD {total_gmv / 1_000:,.0f}K"
        
        return {
            "gmv": {"value": total_gmv, "formatted": gmv_formatted, "change": "+12.5%", "trend": "up"},
            "activeUsers": {"value": active_users, "formatted": f"{active_users:,}", "change": "+8.2%", "trend": "up"},
            "defaultRate": {"value": round(default_rate, 1), "formatted": f"{default_rate:.1f}%", "change": "-0.5%", "trend": "down"},
            "approvalRate": {"value": round(approval_rate, 1), "formatted": f"{approval_rate:.1f}%", "change": "+2.1%", "trend": "up"},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/risk-distribution")
async def get_risk_distribution():
    """Get risk distribution by city/region."""
    try:
        scored_df = pd.read_csv(GOLD_DIR / "uc1_scored_today.csv")
        
        # Group by user_city and calculate risk stats
        risk_by_city = scored_df.groupby("user_city").agg({
            "is_risky_late": "sum",
            "user_id": "count",
            "proba_late_30d": "mean"
        }).reset_index()
        
        risk_by_city.columns = ["city", "high_risk", "total", "avg_risk_prob"]
        risk_by_city["low_risk"] = risk_by_city["total"] - risk_by_city["high_risk"]
        
        # Sort by total and take top 5
        risk_by_city = risk_by_city.nlargest(5, "total")
        
        result = []
        for _, row in risk_by_city.iterrows():
            result.append({
                "city": row["city"],
                "highRisk": int(row["high_risk"]),
                "lowRisk": int(row["low_risk"]),
                "total": int(row["total"]),
                "avgRiskProb": round(row["avg_risk_prob"] * 100, 1)
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/portfolio")
async def get_portfolio_overview():
    """Get portfolio payment status overview."""
    try:
        gold_orders_df = pd.read_csv(GOLD_DIR / "gold_orders_analytics.csv")
        
        # Filter to orders with installments
        orders_with_payments = gold_orders_df[gold_orders_df["installments_count_y"] > 0]
        
        total_installments = orders_with_payments["installments_count_y"].sum()
        paid_installments = orders_with_payments["paid_installments"].sum()
        late_installments = orders_with_payments["late_installments"].sum()
        unpaid_installments = orders_with_payments["unpaid_installments"].sum()
        
        # Calculate on-time (paid but not late)
        on_time = paid_installments - late_installments
        if on_time < 0:
            on_time = 0
        
        total = on_time + late_installments + unpaid_installments
        if total == 0:
            total = 1  # Avoid division by zero
        
        on_time_pct = (on_time / total) * 100
        late_pct = (late_installments / total) * 100
        default_pct = (unpaid_installments / total) * 100
        
        return {
            "onTime": {"value": round(on_time_pct, 1), "formatted": f"{on_time_pct:.1f}%"},
            "late": {"value": round(late_pct, 1), "formatted": f"{late_pct:.1f}%"},
            "defaults": {"value": round(default_pct, 1), "formatted": f"{default_pct:.1f}%"},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard/risky-users")
async def get_risky_users():
    """Get users at risk of late payment, sorted by risk probability (descending)."""
    try:
        scored_df = pd.read_csv(GOLD_DIR / "uc1_scored_today.csv")
        
        # Select important columns and sort by risk probability (descending)
        risky_users = scored_df[[
            "user_id", "user_city", "due_date", "proba_late_30d", 
            "late_payment_rate_90d", "num_active_plans", "status"
        ]].copy()
        
        # Convert risk probability to percentage
        risky_users["risk_pct"] = (risky_users["proba_late_30d"] * 100).round(1)
        risky_users["late_rate_pct"] = (risky_users["late_payment_rate_90d"] * 100).fillna(0).round(1)
        
        # Sort by risk (highest first) and take top 10
        risky_users = risky_users.sort_values("proba_late_30d", ascending=False).head(10)
        
        # Convert to list of dicts with native Python types
        result = []
        for _, row in risky_users.iterrows():
            result.append({
                "userId": str(row["user_id"]),
                "city": str(row["user_city"]) if pd.notna(row["user_city"]) else "Unknown",
                "dueDate": str(row["due_date"]),
                "riskPct": float(row["risk_pct"]),
                "lateRatePct": float(row["late_rate_pct"]),
                "activePlans": int(row["num_active_plans"]) if pd.notna(row["num_active_plans"]) else 0,
                "status": str(row["status"]),
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ===== FEEDBACK FEATURE =====
import csv
from datetime import datetime

FEEDBACK_FILE = PROJECT_ROOT / "data" / "feedback.csv"

class FeedbackRequest(BaseModel):
    query: str
    response_snippet: str
    rating: str  # "positive" or "negative"
    comment: Optional[str] = None

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Save user feedback on AI responses."""
    try:
        # Ensure file exists with header
        file_exists = FEEDBACK_FILE.exists()
        
        with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(["timestamp", "query", "response_snippet", "rating", "comment"])
            
            writer.writerow([
                datetime.now().isoformat(),
                feedback.query[:200],  # Limit query length
                feedback.response_snippet[:300],  # Limit response length
                feedback.rating,
                feedback.comment or ""
            ])
        
        return {"status": "success", "message": "Feedback saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/feedback")
async def get_feedback():
    """Retrieve all feedback entries."""
    try:
        if not FEEDBACK_FILE.exists():
            return {"total": 0, "positive_pct": 0, "entries": []}
        
        entries = []
        with open(FEEDBACK_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entries.append(row)
        
        # Calculate stats
        total = len(entries)
        positive = sum(1 for e in entries if e.get("rating") == "positive")
        positive_pct = round((positive / total * 100) if total > 0 else 0, 1)
        
        return {
            "total": total,
            "positive_pct": positive_pct,
            "entries": entries[-50:]  # Return last 50 entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
