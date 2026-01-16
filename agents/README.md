# BNPL Intelligent Analytics Agent

An AI-powered analytics copilot for BNPL (Buy Now Pay Later) platforms, built with LangChain, LangGraph, and MCP (Model Context Protocol).

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- pip or poetry

### Installation

```bash
# Navigate to agents directory
cd agents

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

```bash
# Create .env file
cp .env.example .env

# Configure your Gemini API key (FREE tier available!)
# Get your key at: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_gemini_api_key_here

# Local data is enabled by default (uses /data/silver/ CSV files)
USE_LOCAL_DATA=true
```

> **Note**: The agent works without an LLM API key (uses rule-based logic), but responses are better with Gemini.

### Running the Agent

```bash
# Interactive mode
python -m src.main

# Run demo scenarios
python -m src.main --demo

# Test specific question
python -m src.main --query "What was our GMV last month?"
```

## 📁 Project Structure

```
agents/
├── config/
│   ├── kpis.yml              # KPI definitions
│   ├── question_bank.yml     # Example questions
│   └── schema_allowlist.yml  # Allowed tables/columns
├── src/
│   ├── graph.py              # LangGraph state machine
│   ├── state.py              # State definitions
│   ├── main.py               # Entry point
│   ├── nodes/                # Graph nodes
│   │   ├── router.py
│   │   ├── planner.py
│   │   ├── executor.py
│   │   ├── validator.py
│   │   └── narrator.py
│   └── tools/                # MCP tool wrappers
│       ├── schema_tool.py
│       ├── kpi_tool.py
│       ├── sql_tool.py
│       ├── risk_tool.py
│       └── trace_tool.py
├── prompts/                  # LLM prompts
├── tests/                    # Unit tests
└── demo/                     # Demo scenarios
```

## 🔧 Architecture

```
User Query → Router → Planner → Executor → Validator → Narrator → Response
                ↓         ↓          ↓
           [Intent]  [Tool Plan] [MCP Calls]
```

### Nodes

1. **Router**: Classifies intent (growth/funnel/risk/merchant/finance)
2. **Planner**: Decides KPI vs SQL tool strategy  
3. **Executor**: Calls MCP tools with guardrails
4. **Validator**: Validates results, retries if needed
5. **Narrator**: Generates structured response

### MCP Tools

| Tool | Purpose |
|------|---------|
| `SchemaTool` | Get allowed tables/columns |
| `KPITool` | Fetch pre-computed KPIs |
| `SQLTool` | Execute read-only SQL queries |
| `RiskTool` | Get risk scores (optional) |
| `TraceTool` | Log to Langfuse (optional) |

## 📊 Supported KPIs

- GMV (Gross Merchandise Value)
- Approval Rate
- Active Users (30d)
- Repeat User Rate
- Late Payment Rate
- Delinquency Buckets
- Dispute Rate
- Refund Rate
- Checkout Conversion Rate
- Repayment Velocity

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src
```

## 📝 License

MIT
