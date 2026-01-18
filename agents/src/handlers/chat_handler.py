"""
Chat Handler - Conversational Responses

Handles greetings, help, and general conversational queries.
"""

from typing import Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from ..state import AgentState


CHAT_PROMPT = """You are a helpful BNPL (Buy Now Pay Later) analytics assistant.
You help users understand their business data, risk scores, and performance metrics.

The user said: {query}

Respond in a friendly, professional manner. If they're asking for help, explain what you can do:
- Business KPIs (GMV, approval rate, late payment rate)
- Risk analysis (risky installments, user risk scores, explanations)
- Data lookups (users, merchants, orders by city/category)
- Comparisons by dimension

Keep your response concise (2-3 sentences max)."""


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
                chain = self.prompt | self.llm
                response = await chain.ainvoke({"query": state.user_query})
                state.response = response.content
            except Exception as e:
                state.response = self._get_fallback_response()
        else:
            state.response = self._get_fallback_response()
        
        return state
    
    def _is_greeting(self, query: str) -> bool:
        """Check if it's a simple greeting."""
        greetings = ["hello", "hi", "hey", "bonjour", "salut", "yo", "sup"]
        return any(query.startswith(g) or query == g for g in greetings)
    
    def _get_greeting_response(self, query: str) -> str:
        """Get a friendly greeting response."""
        return (
            "👋 Hello! I'm your BNPL Analytics Copilot. I can help you with:\n\n"
            "📊 **KPIs**: GMV, approval rate, late payment rate\n"
            "⚠️ **Risk**: Risky installments, user risk explanations\n"
            "🔍 **Lookups**: Users, merchants, orders\n\n"
            "What would you like to know?"
        )
    
    def _get_fallback_response(self) -> str:
        """Fallback response when LLM unavailable."""
        return (
            "I'm your BNPL Analytics assistant. I can help you with:\n"
            "- Business metrics (GMV, approval rate)\n"
            "- Risk analysis (late payment predictions)\n"
            "- Data lookups (users, merchants, orders)\n\n"
            "Try asking: 'What's the total GMV?' or 'Show me risky installments'"
        )
