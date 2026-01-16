"""
Trace Tool - Observability logging via Langfuse.

Provides tracing and logging for agent execution,
enabling debugging, evaluation, and monitoring.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

from .mcp_client import get_mcp_client, MCPResponse


class TracePayload(BaseModel):
    """Payload for trace logging."""
    
    event_type: str
    user_query: Optional[str] = None
    intent: Optional[str] = None
    tool_calls: list[dict] = Field(default_factory=list)
    sql_query: Optional[str] = None
    outputs: Optional[Any] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class TraceTool(BaseTool):
    """
    LangChain tool for logging traces via MCP/Langfuse.
    
    This is an OPTIONAL observability tool. It logs:
    - User queries and classified intents
    - Tool calls and their outputs
    - SQL queries executed
    - Latency metrics
    - Errors and exceptions
    
    Usage:
        tool = TraceTool()
        tool.invoke({
            "event_type": "query_complete",
            "user_query": "What was our GMV?",
            "intent": "growth_analytics",
            "latency_ms": 1234
        })
    """
    
    name: str = "trace_log"
    description: str = """Log observability trace for debugging and monitoring.
    
    This is an internal tool for agent observability. Use it to log:
    - User queries and their classified intents
    - Tool executions and results
    - Errors and performance metrics
    
    Parameters:
    - event_type (required): Type of event (query_start, tool_call, query_complete, error)
    - user_query: The original user question
    - intent: Classified intent (growth_analytics, risk, etc.)
    - tool_calls: List of tools called
    - sql_query: Any SQL executed
    - outputs: Tool outputs
    - latency_ms: Execution time in milliseconds
    - error: Error message if failed
    - metadata: Additional context
    
    Note: This tool is for observability only and does not affect query results.
    """
    
    # Track if Langfuse is available
    _langfuse_available: bool = False
    _langfuse_client: Optional[Any] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._init_langfuse()
    
    def _init_langfuse(self):
        """Initialize Langfuse client if configured."""
        public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        
        if public_key and secret_key:
            try:
                from langfuse import Langfuse
                
                self._langfuse_client = Langfuse(
                    public_key=public_key,
                    secret_key=secret_key,
                    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
                )
                self._langfuse_available = True
            except ImportError:
                pass
    
    def _run(
        self,
        event_type: str,
        user_query: Optional[str] = None,
        intent: Optional[str] = None,
        tool_calls: Optional[list] = None,
        sql_query: Optional[str] = None,
        outputs: Optional[Any] = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Synchronous trace logging."""
        return asyncio.run(self._arun(
            event_type, user_query, intent, tool_calls, 
            sql_query, outputs, latency_ms, error, metadata
        ))
    
    async def _arun(
        self,
        event_type: str,
        user_query: Optional[str] = None,
        intent: Optional[str] = None,
        tool_calls: Optional[list] = None,
        sql_query: Optional[str] = None,
        outputs: Optional[Any] = None,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Log trace to MCP/Langfuse.
        """
        payload = TracePayload(
            event_type=event_type,
            user_query=user_query,
            intent=intent,
            tool_calls=tool_calls or [],
            sql_query=sql_query,
            outputs=outputs,
            latency_ms=latency_ms,
            error=error,
            metadata=metadata or {},
        )
        
        # Try Langfuse first
        if self._langfuse_available and self._langfuse_client:
            try:
                self._log_to_langfuse(payload)
                return f"Trace logged to Langfuse: {event_type}"
            except Exception as e:
                # Fall through to MCP
                pass
        
        # Try MCP
        client = get_mcp_client()
        response: MCPResponse = await client.call(
            "trace.log", 
            payload.model_dump(exclude_none=True)
        )
        
        if response.success:
            return f"Trace logged via MCP: {event_type}"
        
        # Fallback to local logging
        self._log_locally(payload)
        return f"Trace logged locally: {event_type}"
    
    def _log_to_langfuse(self, payload: TracePayload):
        """Log to Langfuse."""
        if not self._langfuse_client:
            return
        
        trace = self._langfuse_client.trace(
            name=payload.event_type,
            input=payload.user_query,
            metadata={
                "intent": payload.intent,
                "tool_calls": payload.tool_calls,
                "sql_query": payload.sql_query,
                **payload.metadata,
            }
        )
        
        if payload.outputs:
            trace.update(output=payload.outputs)
        
        if payload.error:
            trace.update(
                level="ERROR",
                status_message=payload.error,
            )
        
        if payload.latency_ms:
            # Log as generation for latency tracking
            trace.generation(
                name="execution",
                metadata={"latency_ms": payload.latency_ms},
            )
    
    def _log_locally(self, payload: TracePayload):
        """Fallback local logging."""
        import json
        import logging
        
        logger = logging.getLogger("bnpl_agent.trace")
        
        log_data = {
            "timestamp": payload.timestamp,
            "event_type": payload.event_type,
            "intent": payload.intent,
            "latency_ms": payload.latency_ms,
            "error": payload.error,
        }
        
        if payload.error:
            logger.error(json.dumps(log_data))
        else:
            logger.info(json.dumps(log_data))
