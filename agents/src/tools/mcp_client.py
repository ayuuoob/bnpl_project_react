"""
Base MCP Client for connecting to MCP servers.

This module provides the foundation for all MCP tool wrappers,
handling connection, authentication, and request/response processing.
"""

import os
import httpx
from typing import Any, Optional
from pydantic import BaseModel, Field


class MCPClientConfig(BaseModel):
    """Configuration for MCP client."""
    
    server_url: str = Field(
        default_factory=lambda: os.getenv("MCP_SERVER_URL", "http://localhost:8000")
    )
    api_key: Optional[str] = Field(
        default_factory=lambda: os.getenv("MCP_API_KEY")
    )
    timeout: float = Field(default=30.0)


class MCPResponse(BaseModel):
    """Standard MCP response wrapper."""
    
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class MCPClient:
    """
    Base MCP client for communicating with MCP servers.
    
    Handles:
    - Connection management
    - Authentication
    - Request/response serialization
    - Error handling
    """
    
    def __init__(self, config: Optional[MCPClientConfig] = None):
        self.config = config or MCPClientConfig()
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def headers(self) -> dict:
        """Build request headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create async HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.config.server_url,
                headers=self.headers,
                timeout=self.config.timeout,
            )
        return self._client
    
    async def call(
        self,
        method: str,
        params: Optional[dict] = None,
    ) -> MCPResponse:
        """
        Call an MCP method.
        
        Args:
            method: MCP method name (e.g., "schema.get", "sql.run")
            params: Method parameters
            
        Returns:
            MCPResponse with success status and data/error
        """
        client = await self._get_client()
        
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {},
            "id": 1,
        }
        
        try:
            response = await client.post("/mcp", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            if "error" in result:
                return MCPResponse(
                    success=False,
                    error=result["error"].get("message", "Unknown error"),
                    metadata={"code": result["error"].get("code")},
                )
            
            return MCPResponse(
                success=True,
                data=result.get("result"),
                metadata={"id": result.get("id")},
            )
            
        except httpx.HTTPStatusError as e:
            return MCPResponse(
                success=False,
                error=f"HTTP error: {e.response.status_code}",
                metadata={"status_code": e.response.status_code},
            )
        except httpx.RequestError as e:
            return MCPResponse(
                success=False,
                error=f"Request error: {str(e)}",
            )
        except Exception as e:
            return MCPResponse(
                success=False,
                error=f"Unexpected error: {str(e)}",
            )
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None


# Singleton client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """Get the singleton MCP client instance."""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client
