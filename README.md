# BNPL Intelligent Analytics 🚀

A comprehensive analytics dashboard and AI-powered copilot for Buy Now Pay Later (BNPL) platforms. This solution helps businesses monitor risk, track KPIs, and interact with their data using natural language.

---

## 🏗️ Architecture

The project follows a modern 3-tier architecture:

1.  **Frontend (UI Layer)**
    *   **Tech**: React, TypeScript, Tailwind CSS, Vite.
    *   **Role**: Interactive dashboard for visualizing KPIs, risk scores, and chatting with the AI Copilot.
    *   **Features**: Role-Based Access Control (RBAC), Interactive Charts (Recharts), Chat Interface.

2.  **Backend (API Layer)**
    *   **Tech**: Python, FastAPI.
    *   **Role**: Serves API endpoints for the frontend and acts as a bridge to the AI agents.
    *   **Endpoints**: `/api/chat` (AI Co-pilot), `/api/dashboard` (KPI Data).

3.  **AI Agents (Intelligence Layer)**
    *   **Tech**: LangChain, Google Gemini Pro.
    *   **Structure**: Graph-based multi-agent system.
        *   **Router**: Classifies user intent (Risk, KPI, Lookup, Conversation).
        *   **Planner**: Orchestrates the execution flow.
        *   **Executor**: Fetches data from CSV/SQL sources.
        *   **Validator**: Ensuring data quality and safety.
        *   **Narrator**: Generates human-friendly insights.

---

## 🛠️ Prerequisites

Before running the project, ensure you have the following installed:

*   **Node.js** (v18 or higher)
*   **Python** (v3.11 or higher)
*   **Google Gemini API Key** (Required for the AI Copilot)

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd bnpl-intelligent-analytics
```

### 2. Backend & Agent Setup
The backend and agents share the same Python environment.

```bash
# Navigate to backend directory
cd webapp/backend

# Create virtual environment (optional but recommended)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies (from root or agent folder)
pip install -r requirements.txt
# OR manually:
pip install fastapi uvicorn pandas langchain-google-genai python-dotenv
```

### 3. Configure API Key
Create a `.env` file in `bnpl-intelligent-analytics/agents/.env` and add your key:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
```

### 4. Frontend Setup
```bash
# Navigate to frontend directory
cd webapp/frontend

# Install dependencies
npm install
```

---

## ▶️ Running the Application

You need to run both the backend and frontend servers simultaneously.

### Terminal 1: Backend Server (Port 8002)
```bash
cd webapp/backend
python main.py
```
*The backend API will run at `http://localhost:8002`.*

### Terminal 2: Frontend Server (Port 5173)
```bash
cd webapp/frontend
npm run dev
```
*The application will be accessible at `http://localhost:5173`.*

---

## 🔑 User Accounts (RBAC)

Use these credentials to test different roles:

| Role | Email | Password | Access |
|------|-------|----------|--------|
| **Admin (CEO)** | `ceo@bnpl.com` | `ceo123` | Full Access (Dashboard, Copilot, Docs, Feedback) |
| **Analyst** | `analyst@bnpl.com` | `analyst123` | Analytics & Copilot (No Feedback) |
| **Developer** | `dev@bnpl.com` | `dev123` | Dashboard, Docs, Feedback (No Copilot) |
| **Viewer** | `viewer@bnpl.com` | `viewer123` | Dashboard Only |

---

## 💡 Key Features

*   **🔍 AI Copilot**: Ask questions like *"Show me high risk users in Rabat"* or *"What is our current GMV?"*.
*   **📊 Dynamic Dashboards**: Real-time visualization of risk distribution and sales performance.
*   **🛡️ Risk Scoring**: ML-based risk assessment for every installment and user.
*   **🔐 Role-Based Security**: Granular access control for sensitive data and features.