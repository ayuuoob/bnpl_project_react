# BNPL Intelligent Analytics 🚀

A comprehensive analytics dashboard and AI-powered copilot for Buy Now Pay Later (BNPL) platforms. This solution helps businesses monitor risk, track KPIs, and interact with their data using natural language, powered by Google Gemini Pro and a sophisticated LangGraph agent.

---

## 📚 Table of Contents
1.  [Architecture](#-architecture)
2.  [Key Features](#-key-features)
3.  [Prerequisites](#-prerequisites)
4.  [Installation & Setup](#-installation--setup)
5.  [Running the Application](#-running-the-application)
6.  [User Roles (RBAC)](#-user-accounts-rbac)
7.  [Troubleshooting](#-troubleshooting)

---

## 🏗️ Architecture

The project follows a modern **Hybrid Micro-service** architecture, decoupled into a React Frontend and a FastAPI Backend/Agent layer.

```mermaid
graph TD
    User((User)) -->|Interact| Frontend[React Frontend]
    Frontend -->|API Requests| Backend[FastAPI Backend]
    
    subgraph "Intelligent Core"
        Backend -->|Orchestrate| AgentGraph[LangGraph Agent]
        AgentGraph -->|Plan| Router[Planner]
        AgentGraph -->|Act| Executor[Executor]
        AgentGraph -->|Check| Validator[Validator]
        AgentGraph -->|Speak| Narrator[Narrator]
    end
    
    subgraph "Data Layer"
        Backend -->|Read| Silver[Silver Data (CSV)]
        Backend -->|Read| Gold[Gold Data (Analytics)]
    end

    AgentGraph -.->|LLM Calls| Gemini[Google Gemini API]
```

### 1. Frontend Layer (UI)
*   **Path**: `webapp/frontend`
*   **Tech**: React, TypeScript, Tailwind CSS, Vite.
*   **Responsibilities**:
    *   **Dashboard**: Renders real-time charts (Recharts) from Gold data.
    *   **Copilot Interface**: Manages chat state and sends **Conversation History** (last 10 messages) to the backend for context-aware AI.
    *   **Security**: Handles JWT-based (simulated) RBAC to restrict views (e.g., Viewers cannot see the Copilot).

### 2. Backend Layer (API)
*   **Path**: `webapp/backend`
*   **Tech**: Python 3.11, FastAPI, Uvicorn.
*   **Responsibilities**:
    *   **API Gateway**: Exposes REST endpoints (`/api/chat`, `/api/dashboard/*`).
    *   **State Management**: Maintains the global `BNPLCopilot` instance.
    *   **Data Access**: Uses `pandas` to query local CSV data with high performance.

### 3. Agentic Layer (The Brain)
*   **Path**: `agents/src`
*   **Tech**: LangChain, LangGraph, Google Gemini 1.5 Flash.
*   **Pipeline**:
    1.  **Planner/Router**: Classifies intent (Risk vs. Sales vs. Chat). Uses LLM with Regex fallback.
    2.  **Executor**: The "Hands". Executes Python tools to fetch and filter data (e.g., `get_risky_users(city='Rabat')`).
    3.  **Validator**: The "Eyes". Checks data quality, summarizes large datasets, and catches errors.
    4.  **Narrator**: The "Voice". Generates professional, executive-level natural language responses using the query, data summary, and conversation history.

---

## 💡 Key Features

*   **🔍 Context-Aware AI Copilot**: 
    *   Remembers your conversation. Ask "Show me risky users", then "Filter *them* by city".
    *   Explains concepts like "What is Risk Score?" using an internal knowledge base + LLM.
*   **📊 Dynamic Monitoring**: 
    *   Real-time tracking of GMV, Approval Rates, and Default Rates.
    *   Interactive maps and charts for geographic risk analysis.
*   **🛡️ Risk Scoring Engine**: 
    *   ML-based prediction of late payments (0-100% probability).
*   **🔐 Role-Based Access Control (RBAC)**: 
    *   **CEO/Admin**: Full visibility.
    *   **Analyst**: Data & AI access only.
    *   **Viewer**: Read-only Dashboard access.

---

## 🛠️ Prerequisites

*   **Node.js**: v18 or higher (for Frontend).
*   **Python**: v3.11 or higher (for Backend).
*   **Google Gemini API Key**: Required for the Copilot. [Get one here](https://aistudio.google.com/).

---

## 🚀 Installation & Setup

### 1. Clone the Project
```bash
git clone <repository-url>
cd bnpl-intelligent-analytics
```

### 2. Backend Setup
```bash
cd webapp/backend

# Create virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# (If requirements.txt is missing, install manually):
# pip install fastapi uvicorn pandas langchain-google-genai python-dotenv langchain
```

### 3. Configure API Key
Create a `.env` file in `agents/.env`:
```env
GOOGLE_API_KEY=your_actual_api_key_here
```

### 4. Frontend Setup
```bash
# Open a new terminal
cd webapp/frontend
npm install
```

---

## ▶️ Running the Application

### Step 1: Start Backend
```bash
# In webapp/backend
python main.py
```
> Server runs on **http://localhost:8002**

### Step 2: Start Frontend
```bash
# In webapp/frontend
npm run dev
```
> App runs on **http://localhost:5173**

---

## 🔑 User Accounts (RBAC)

Use these credentials to test the different personas:

| Role | Email | Password | Permissions |
|------|-------|----------|-------------|
| **Admin (CEO)** | `ceo@bnpl.com` | `ceo123` | **Top Tier**: Can see everything, export reports, and chat with AI. |
| **Analyst** | `analyst@bnpl.com` | `analyst123` | **Data Focus**: Can use Copilot and export data, but cannot change settings. |
| **Developer** | `dev@bnpl.com` | `dev123` | **Tech Focus**: Access to logs and system settings. |
| **Viewer** | `viewer@bnpl.com` | `viewer123` | **Restricted**: Can ONLY view the dashboard. No AI Copilot. |

---

## 🔧 Troubleshooting

*   **"Error connecting to backend"**: Ensure `main.py` is running on port 8002. Check the console for Python errors.
*   **"Poor response / Fallback mode"**: 
    *   Check your `.env` file has a valid `GOOGLE_API_KEY`.
    *   Ensure the model in `graph.py` is set to `gemini-1.5-flash` (not a Llama model).
*   **"API Exhausted"**: The system has smart fallbacks. Try asking basic definition questions ("What is GMV?") which work offline.

---
**Built for the DXC Hackathon 2024**