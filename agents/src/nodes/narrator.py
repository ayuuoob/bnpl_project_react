from typing import Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from ..state import AgentState, Intent

# The prompt is exactly the same as in graph.py to ensure identical answers
RESPONSE_PROMPT = """You are a BNPL analytics assistant. Generate a clear, executive-friendly response based on the SUMMARY DATA provided.

User Question: {query}
Intent: {intent}
Data Summary: {data}
Filters Applied: {filters}
Explanation Needed: {explain}

IMPORTANT GUIDELINES:
1. **NO ALLUCINATIONS**: If the data is empty or not provided, say "I don't have that data" or "No data found".
2. **CONTEXT**: The user sees the full data table in the UI. DO NOT attempt to list items.
3. **INSIGHTS**: Your job is to interpret the summary stats provided above (Total Amount, Averages, Counts).
4. **Predictive Language**: Always say "the model PREDICTS" or "ML model indicates" - never state risk as absolute fact.
5. **Chart Recommendations**: Suggest appropriate charts when data visualization would help:
   - Risk distribution → Donut chart or histogram
   - Top risky items → Bar chart
   - Trends → Line chart
   - Comparisons → Bar chart or table
6. **Be concise**: 2-4 sentences summary, then data/charts.
7. **If Explanation Needed** is "Yes", include a short paragraph explaining the meaning of the requested metric or data.

RESPONSE FORMAT (use exactly this structure):
📊 **[Title]**

[Brief 1-2 sentence explanation using PREDICTIVE language. Explicitly mention applied filters if any.]

[Markdown TABLE if showing list data]

💡 **Insight**: [Key takeaway from the summary stats]

📈 **Recommended Chart**: [chart_type] to visualize [what]

Respond now:"""

class NarratorNode:
    """
    Narrator Node (The "Voice").
    
    Responsibilities:
    1. Construct the prompt with context (filters, explanation need).
    2. Call the LLM to generate the natural language response.
    3. Ensure the voice is consistent (Executive-friendly, Predictive).
    """
    
    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(RESPONSE_PROMPT)

    async def generate_response(self, state: AgentState, data_summary: str, filters: str, explain_needed: str) -> str:
        """Generate the narrative response using LLM."""
        if not self.llm:
            return "Error: LLM not initialized."

        try:
            chain = self.prompt | self.llm
            result = await chain.ainvoke({
                "query": state.user_query,
                "intent": state.intent.value,
                "data": data_summary,
                "filters": filters,
                "explain": explain_needed
            })
            return result.content
        except Exception as e:
            print(f"[Narrator] Generation error: {e}")
            raise e
