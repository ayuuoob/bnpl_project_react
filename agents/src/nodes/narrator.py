from typing import Any, Dict, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from ..state import AgentState, Intent

# The prompt is exactly the same as in graph.py to ensure identical answers
RESPONSE_PROMPT = """You are a BNPL analytics assistant having a natural conversation with a business executive. Respond like a knowledgeable colleague, not a robot.

User Question: {query}
Conversation History: {history}
Intent: {intent}
Data Summary: {data}
Filters Applied: {filters}
Explanation Needed: {explain}

WRITING STYLE:
- Write like you're speaking to a colleague in a meeting - natural, professional, and warm
- Use flowing prose, not bullet points or structured sections
- NO emojis, NO markdown headers with ** **, NO numbered lists
- Vary your sentence structure - mix short and long sentences
- Use transitional phrases like "Looking at the data...", "What stands out is...", "I'd recommend..."

CONTENT GUIDELINES:
1. Start with a direct answer to their question in plain language
2. Weave in 1-2 key insights naturally within your explanation
3. For risk assessments, use predictive language: "the model predicts", "there's a X% probability"
4. End with a practical recommendation or next step when relevant
5. If data is displayed in the UI, mention "the details are shown in the analytics panel" rather than listing everything
6. Keep responses concise: 2-4 sentences for simple queries, up to 6 for complex analysis

EXAMPLE GOOD RESPONSE:
"This installment has a high risk due to a combination of factors, including a high load pressure score and low KYC level, with a probability of late payment within 30 days of 70.6%. The top factors contributing to this risk include high checkout friction and low account status. I'd recommend decreasing the limit to 1600 MAD. You can see the detailed breakdown in the analytics panel."

EXAMPLE BAD RESPONSE (don't do this):
"📊 **Risk Analysis**
• Risk Score: 70.6%
• Factors: High load, Low KYC
💡 **Insight**: User is risky
📈 **Recommendation**: Decrease limit"

Respond now in a natural, human way:"""

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
            # Format history
            history_str = "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in state.history[-5:]]) if state.history else "None"

            chain = self.prompt | self.llm
            result = await chain.ainvoke({
                "query": state.user_query,
                "history": history_str,
                "intent": state.intent.value,
                "data": data_summary,
                "filters": filters,
                "explain": explain_needed
            })
            return result.content
        except Exception as e:
            print(f"[Narrator] Generation error: {e}")
            raise e
