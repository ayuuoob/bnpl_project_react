"""
BNPL Intelligent Analytics - Copilot UI
Matching Reference Design with:
- Left sidebar with chat history
- Center full-height chat
- Right analytics panel with tabs
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os
from pathlib import Path
from datetime import datetime
import json
import asyncio
import io
import base64

# Fix path
WEBAPP_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = WEBAPP_DIR.parent
AGENTS_PATH = PROJECT_ROOT / "agents"
DATA_PATH = PROJECT_ROOT / "data"

sys.path.insert(0, str(AGENTS_PATH))
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(AGENTS_PATH / ".env")

# Import agent
from src.graph import run_query_with_chart_sync, get_copilot

# Page config
st.set_page_config(
    page_title="BNPL Copilot",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===== CUSTOM CSS - MATCHING REFERENCE DESIGN =====
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #1a1a4e 50%, #24243e 100%);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a4e 0%, #0f0c29 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: white;
    }
    
    /* Hide default streamlit elements */
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Container padding */
    .main .block-container {
        padding: 1rem;
        max-width: 100%;
    }
    
    /* New chat button */
    .new-chat-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 12px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        width: 100%;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Chat history items */
    .chat-history-item {
        color: rgba(255,255,255,0.7);
        padding: 10px 12px;
        border-radius: 8px;
        margin: 4px 0;
        cursor: pointer;
        font-size: 0.9rem;
        text-overflow: ellipsis;
        overflow: hidden;
        white-space: nowrap;
    }
    
    .chat-history-item:hover {
        background: rgba(255,255,255,0.1);
    }
    
    /* Main chat container */
    .chat-container {
        background: rgba(255,255,255,0.03);
        border-radius: 16px;
        padding: 20px;
        height: calc(100vh - 140px);
        display: flex;
        flex-direction: column;
    }
    
    /* Chat header */
    .chat-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 20px;
        padding-bottom: 16px;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    .chat-header h2 {
        color: white;
        margin: 0;
        font-size: 1.3rem;
        font-weight: 600;
    }
    
    .chat-header span {
        color: rgba(255,255,255,0.5);
        font-size: 0.85rem;
    }
    
    /* Chat messages area */
    .messages-area {
        flex: 1;
        overflow-y: auto;
        padding: 10px 0;
    }
    
    /* User message - right aligned, purple bubble */
    .user-bubble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 18px;
        border-radius: 20px 20px 4px 20px;
        max-width: 75%;
        margin: 10px 0 10px auto;
        font-size: 0.95rem;
        display: inline-block;
        float: right;
        clear: both;
    }
    
    /* Agent message - left aligned, gray bubble */
    .agent-bubble {
        background: rgba(255,255,255,0.08);
        color: rgba(255,255,255,0.9);
        padding: 14px 18px;
        border-radius: 20px 20px 20px 4px;
        max-width: 80%;
        margin: 10px auto 10px 0;
        font-size: 0.95rem;
        display: block;
        clear: both;
    }
    
    .agent-bubble a {
        color: #667eea;
        text-decoration: none;
    }
    
    /* Analytics panel */
    .analytics-panel {
        background: white;
        border-radius: 16px;
        height: calc(100vh - 140px);
        overflow: hidden;
    }
    
    .analytics-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 16px 20px;
        border-bottom: 1px solid #eee;
    }
    
    .analytics-header h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
        color: #1a1a2e;
    }
    
    /* Analytics tabs */
    .analytics-tabs {
        display: flex;
        gap: 8px;
        padding: 12px 20px;
        border-bottom: 1px solid #eee;
    }
    
    .tab-btn {
        padding: 8px 16px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-size: 0.9rem;
        background: #f5f5f5;
        color: #666;
    }
    
    .tab-btn.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* KPI Cards */
    .kpi-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        padding: 20px;
    }
    
    .kpi-card {
        background: #f8f9fc;
        border-radius: 12px;
        padding: 16px;
        border: 1px solid #eee;
    }
    
    .kpi-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 12px;
        font-size: 1.2rem;
    }
    
    .kpi-icon.orange { background: rgba(255,159,67,0.15); }
    .kpi-icon.blue { background: rgba(102,126,234,0.15); }
    .kpi-icon.green { background: rgba(81,207,102,0.15); }
    .kpi-icon.red { background: rgba(255,107,107,0.15); }
    
    .kpi-label {
        color: #888;
        font-size: 0.85rem;
        margin-bottom: 4px;
    }
    
    .kpi-value {
        color: #1a1a2e;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    .kpi-unit {
        color: #888;
        font-size: 0.9rem;
        font-weight: 400;
    }
    
    /* Chart container */
    .chart-section {
        padding: 20px;
        border-top: 1px solid #eee;
    }
    
    .chart-title {
        font-size: 1rem;
        font-weight: 600;
        color: #1a1a2e;
        margin-bottom: 16px;
    }
    
    /* Input area */
    .input-container {
        padding: 16px;
        border-top: 1px solid rgba(255,255,255,0.1);
        background: rgba(0,0,0,0.2);
        border-radius: 0 0 16px 16px;
    }
    
    /* Override Streamlit input */
    .stTextInput input {
        background: rgba(255,255,255,0.1) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 12px !important;
        color: white !important;
        padding: 14px 18px !important;
    }
    
    .stTextInput input::placeholder {
        color: rgba(255,255,255,0.5) !important;
    }
    
    /* Streamlit tabs override for right panel */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background: white;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: #666;
        padding: 12px 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background: transparent;
        color: #667eea;
        border-bottom: 2px solid #667eea;
    }
    
    /* Override for analytics panel background */
    [data-testid="column"]:last-child {
        background: white;
        border-radius: 16px;
        padding: 0 !important;
    }
    
    /* Date section */
    .date-label {
        color: rgba(255,255,255,0.5);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin: 16px 0 8px 0;
    }
</style>
""", unsafe_allow_html=True)


# ===== SESSION STATE =====
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = None
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = 0


# ===== CHART CREATION =====
def create_chart(chart_data: dict) -> go.Figure:
    """Create Plotly chart from chart_data."""
    if not chart_data:
        return None
    
    chart_type = chart_data.get("type", "bar")
    labels = chart_data.get("labels", [])
    values = chart_data.get("values", [])
    title = chart_data.get("title", "")
    
    if chart_type == "bar":
        fig = go.Figure(data=[go.Bar(
            x=labels[:10],
            y=values[:10],
            marker_color=chart_data.get("color", "#667eea"),
            text=[f"{v:.1f}" if isinstance(v, float) else str(v) for v in values[:10]],
            textposition='outside'
        )])
    elif chart_type == "donut":
        colors = chart_data.get("colors", ["#667eea", "#51cf66"])
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.5,
            marker_colors=colors
        )])
    elif chart_type == "gauge":
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=chart_data.get("value", 0),
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#667eea"},
                'steps': [
                    {'range': [0, 40], 'color': '#51cf66'},
                    {'range': [40, 70], 'color': '#ffc107'},
                    {'range': [70, 100], 'color': '#ff6b6b'}
                ]
            }
        ))
    else:
        return None
    
    fig.update_layout(
        height=250,
        margin=dict(t=30, b=30, l=30, r=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(size=11)
    )
    
    return fig


def extract_kpis(data: dict) -> list:
    """Extract KPIs from data."""
    if not data:
        return []
    
    kpis = []
    data_type = data.get("type", "")
    
    if data_type == "high_risk_users":
        summary = data.get("summary", {})
        highlight = data.get("highlight", {})
        kpis.append({"label": "High Risk Users", "value": str(data.get("count", 0)), "icon": "⚠️", "color": "orange"})
        kpis.append({"label": "Highest Risk", "value": f"{highlight.get('risk_score', 0)}%", "icon": "🎯", "color": "red"})
        kpis.append({"label": "Avg Risk Score", "value": f"{summary.get('avg_risk_score', 0)}%", "icon": "📊", "color": "blue"})
    
    elif data_type == "risk_overview":
        kpis.append({"label": "High Risk Users", "value": str(data.get("high_risk_count", 0)), "icon": "⚠️", "color": "orange"})
        kpis.append({"label": "Total Installments", "value": str(data.get("total_installments", 0)), "icon": "📊", "color": "blue"})
        kpis.append({"label": "Avg Risk Score", "value": f"{data.get('avg_risk_score', 0)}%", "icon": "📈", "color": "green"})
        kpis.append({"label": "Risk Rate", "value": f"{data.get('high_risk_pct', 0)}%", "icon": "🎯", "color": "red"})
    
    elif data_type == "user_risk_list":
        summary = data.get("summary", {})
        kpis.append({"label": "Users Analyzed", "value": str(data.get("count", 0)), "icon": "👥", "color": "blue"})
        kpis.append({"label": "High Risk Users", "value": str(summary.get("high_risk_users", 0)), "icon": "⚠️", "color": "red"})
        kpis.append({"label": "Avg Risk Score", "value": f"{summary.get('avg_risk_score', 0)}%", "icon": "📊", "color": "orange"})
    
    elif data_type == "trust_score":
        kpis.append({"label": "Trust Score", "value": str(data.get("trust_score", 0)), "icon": "🎯", "color": "green"})
        kpis.append({"label": "Decision", "value": data.get("decision", "N/A")[:10], "icon": "📋", "color": "blue"})
        kpis.append({"label": "Risk %", "value": f"{data.get('risk_probability', 0)}%", "icon": "⚠️", "color": "red"})
    
    return kpis


# ===== SIDEBAR =====
with st.sidebar:
    # New Chat Button
    if st.button("➕ New chat", use_container_width=True, type="primary"):
        st.session_state.messages = []
        st.session_state.analytics_data = None
        st.session_state.current_chat_id += 1
        st.rerun()
    
    # Search
    st.text_input("🔍 Search chats...", placeholder="Search", key="search_chats", label_visibility="collapsed")
    
    # Chat History
    st.markdown('<div class="date-label">TODAY</div>', unsafe_allow_html=True)
    
    # Show recent queries as history
    if st.session_state.messages:
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        for i, msg in enumerate(user_msgs[-5:]):
            preview = msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
            st.markdown(f'<div class="chat-history-item">💬 {preview}</div>', unsafe_allow_html=True)


# ===== MAIN LAYOUT =====
col_chat, col_analytics = st.columns([6, 4])

# ===== CHAT COLUMN =====
with col_chat:
    # Header
    st.markdown("""
        <div class="chat-header">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); width: 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center;">📊</div>
            <div>
                <h2>BNPL Copilot</h2>
                <span>Powered by Gemini & Local Pandas</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Messages container
    chat_container = st.container(height=500)
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
                <div class="agent-bubble">
                    👋 Hello! I'm your BNPL Analytics Copilot.<br><br>
                    I can help you with:<br>
                    • Risk analysis and predictions<br>
                    • User and merchant lookups<br>
                    • KPIs and business metrics<br><br>
                    Try asking: <b>"Who is the most risky user?"</b>
                </div>
            """, unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f'<div class="user-bubble">{msg["content"]}</div><div style="clear:both;"></div>', unsafe_allow_html=True)
            else:
                content = msg["content"].replace("\n", "<br>")
                st.markdown(f"""
                    <div class="agent-bubble">
                        {content}
                        <br><br>
                        <a href="#">📊 View analysis</a>
                    </div>
                """, unsafe_allow_html=True)
    
    # Input
    query = st.chat_input("Ask about GMV, users, merchants, or risk...")
    
    if query:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": query})
        
        # Process
        with st.spinner("Analyzing..."):
            try:
                result = run_query_with_chart_sync(query)
                response = result.get("response", "I couldn't process that query.")
                chart_data = result.get("chart_data")
                
                copilot = get_copilot()
                raw_data = getattr(copilot, '_last_data', None)
                
                st.session_state.analytics_data = {
                    "response": response,
                    "chart_data": chart_data,
                    "raw_data": raw_data,
                    "query": query
                }
                
                st.session_state.messages.append({"role": "agent", "content": response})
            except Exception as e:
                st.session_state.messages.append({"role": "agent", "content": f"Error: {e}"})
        
        st.rerun()


# ===== ANALYTICS COLUMN =====
with col_analytics:
    st.markdown("""
        <div style="background: white; border-radius: 16px; min-height: calc(100vh - 140px); overflow: hidden;">
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #eee;">
                <h3 style="margin: 0; font-size: 1.1rem; font-weight: 600; color: #1a1a2e;">Analytics</h3>
                <span style="color: #888; cursor: pointer;">✕</span>
            </div>
    """, unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "📈 Charts", "📋 Details"])
    
    with tab1:
        data = st.session_state.analytics_data.get("raw_data", {}) if st.session_state.analytics_data else {}
        kpis = extract_kpis(data)
        
        if kpis:
            # KPI Grid
            cols = st.columns(2)
            for i, kpi in enumerate(kpis[:4]):
                with cols[i % 2]:
                    color_class = kpi.get("color", "blue")
                    st.markdown(f"""
                        <div class="kpi-card">
                            <div class="kpi-icon {color_class}">{kpi['icon']}</div>
                            <div class="kpi-label">{kpi['label']}</div>
                            <div class="kpi-value">{kpi['value']}</div>
                        </div>
                    """, unsafe_allow_html=True)
        else:
            # Default KPIs
            cols = st.columns(2)
            with cols[0]:
                st.metric("High Risk Users", "1000", "↑ 5%")
                st.metric("Avg Risk Score", "58.3%", "↓ 2%")
            with cols[1]:
                st.metric("Total Users", "35", "")
                st.metric("Approval Rate", "55.0%", "↑ 3%")
        
        # Chart
        chart_data = st.session_state.analytics_data.get("chart_data") if st.session_state.analytics_data else None
        if chart_data:
            st.markdown(f"**{chart_data.get('title', 'Chart')}**")
            fig = create_chart(chart_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="overview_chart")
    
    with tab2:
        chart_data = st.session_state.analytics_data.get("chart_data") if st.session_state.analytics_data else None
        if chart_data:
            fig = create_chart(chart_data)
            if fig:
                st.plotly_chart(fig, use_container_width=True, key="charts_tab")
        else:
            st.info("Run a query to see charts here")
    
    with tab3:
        data = st.session_state.analytics_data.get("raw_data", {}) if st.session_state.analytics_data else {}
        if data and "items" in data:
            df = pd.DataFrame(data["items"])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No data table available")
    
    st.markdown("</div>", unsafe_allow_html=True)
