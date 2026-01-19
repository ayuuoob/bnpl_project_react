"""
Chat Handler - Conversational Responses

Handles greetings, help, and general conversational queries.
"""

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from ..state import AgentState


CHAT_PROMPT = """You are an expert BNPL (Buy Now Pay Later) analytics assistant.
You help business users understand their data, risk models, and key performance indicators.

The user said: {query}

Conversation History:
{history}

Guidelines:
1. If the user asks for a definition (e.g., "What is risk?", "Explain GMV"), provide a clear, professional explanation tailored to the BNPL context.
2. If asking about the system/models, explain that we use Machine Learning to predict late payment probability based on behavior and history.
3. If it's a greeting, be warm and concise.
4. If they ask for specific data (numbers, lists), politely guide them to ask specific questions like "Show me the total GMV" or "List risky users".

Tone: Professional, helpful, knowledgeable.
"""


class ChatHandler:
    """Handler for conversational queries."""
    
    def __init__(self, llm: Optional[ChatGoogleGenerativeAI] = None):
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_template(CHAT_PROMPT)
    
    async def handle(self, state: AgentState) -> AgentState:
        """Handle conversational query."""
        query = state.user_query.strip().lower()
        
        # Quick responses for common greetings
        if self._is_greeting(query):
            state.response = self._get_greeting_response(query)
            return state
        
        # Use LLM for other conversations
        if self.llm:
            try:
                # Format history
                history_str = "\n".join([f"{msg['role'].title()}: {msg['content']}" for msg in state.history[-5:]]) if state.history else "None"
                
                chain = self.prompt | self.llm
                response = await chain.ainvoke({
                    "query": state.user_query,
                    "history": history_str
                })
                state.response = response.content
            except Exception as e:
                state.response = self._get_fallback_response(state.user_query)
        else:
            state.response = self._get_fallback_response(state.user_query)
        
        return state
    
    def _is_greeting(self, query: str) -> bool:
        """Check if it's a simple greeting."""
        greetings = ["hello", "hi", "hey", "bonjour", "salut", "yo", "sup"]
        return any(query.startswith(g) or query == g for g in greetings)
    
    def _get_greeting_response(self, query: str) -> str:
        """Get a friendly greeting response."""
        return (
            "Hello! I'm your BNPL Analytics Copilot. I can help you explore your portfolio data, "
            "analyze risk scores and late payment predictions, look up specific users or merchants, "
            "and pull KPIs like GMV and approval rates. What would you like to know?"
        )
    
    def _get_fallback_response(self, query: str = "") -> str:
        """Fallback response when LLM unavailable - now with basic smarts."""
        q_lower = query.lower()
        
        # Offline Knowledge Base
        if "risk" in q_lower and "trust" in q_lower:
             return (
                 "**Risk vs Trust Score:**\n"
                 "- **Risk Score**: Predicts the probability of *late payment*. Higher score = Higher risk (bad).\n"
                 "- **Trust Score**: Measures user reliability based on successful repayments. Higher score = More trust (good).\n"
                 "They are inverse metrics used to approve or reject orders."
             )
        
        if "risk" in q_lower and "what" in q_lower:
            return (
                "**Risk Score Explanation:**\n"
                "The Risk Score is a probability (0-100%) indicating how likely a user or installment is to miss a payment.\n"
                "It is calculated using a Machine Learning model that analyzes payment history, account age, and behavioral patterns."
            )
            
        if "gmv" in q_lower:
            return (
                "**GMV (Gross Merchandise Value):**\n"
                "This represents the total value of merchandise sold through the BNPL platform over a specific period.\n"
                "It's a key indicator of business growth and volume."
            )
            
        if "model" in q_lower or "work" in q_lower:
             return (
                 "**How the Model Works:**\n"
                 "We use a Gradient Boosting (XGBoost) model trained on historical repayment data.\n"
                 "It looks at features like 'days since first order', 'average purchase value', and 'failed transaction count' to predict future default risk."
             )

        return (
            "I'm currently unable to access my online brain, but I can help with basic data.\n"
            "Try asking for specific numbers like 'Show me the total GMV' or 'List risky users' which I can fetch directly from the database."
        )
