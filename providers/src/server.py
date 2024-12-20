import asyncio
from typing import Any, Dict, Optional, Union

import uvicorn
from adapter_interface import AdapterInterface, AdapterRequest
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from uniswap_provider import OutputType

app = FastAPI(
    title="Uniswap Provider API",
    description="API for interacting with Uniswap pools and swaps",
    version="1.0.0"
)

# Store the adapter interface instance
adapter: Optional[AdapterInterface] = None

class QueryRequest(BaseModel):
    network: str
    output_type_id: int
    prompt: str
    category_id: int = 1
    name: Optional[str] = "Uniswap Query"
    description: Optional[str] = ""
    variables: Optional[str] = ""

@app.on_event("startup")
async def startup_event():
    """Initialize the adapter when the server starts"""
    global adapter
    adapter = await AdapterInterface().initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when the server shuts down"""
    global adapter
    if adapter:
        await adapter.close()

@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {"status": "ok", "service": "Uniswap Provider API"}

@app.post("/query")
async def query(request: QueryRequest):
    """
    Process a query request
    
    Args:
        request: QueryRequest object containing the query parameters
        
    Returns:
        The processed result based on the output type
    """
    try:
        if not adapter:
            raise HTTPException(status_code=503, detail="Service not initialized")

        # Create adapter request
        adapter_request = AdapterRequest(
            name=request.name,
            network=request.network,
            description=request.description,
            variables=request.variables,
            category_id=request.category_id,
            output_type_id=request.output_type_id,
            prompt=request.prompt
        )

        # Process the request
        result = await adapter.process_request(adapter_request)
        
        # Format the response based on the result type
        if isinstance(result, dict):
            # Handle the new format with explanation and value
            if isinstance(result["value"], bytes):
                # Convert bytes to hex string with 0x prefix
                result["value"] = "0x" + result["value"].hex()
            return result
        else:
            # Handle legacy format (should be removed once all code is updated)
            if isinstance(result, bytes):
                return {"result": "0x" + result.hex()}
            elif isinstance(result, (bool, int)):
                return {"result": result}
            elif isinstance(result, tuple):
                return {"result": {"message": result[0], "success": result[1]}}
            else:
                return {"result": result}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/supported_networks")
async def get_supported_networks():
    """Get list of supported networks"""
    try:
        if not adapter:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        return {
            "networks": [
                {"name": "BASE", "chain_id": 8453},
                {"name": "ARBITRUM", "chain_id": 42161},
                {"name": "RIVALZ", "chain_id": 1234}
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/output_types")
async def get_output_types():
    """Get list of supported output types"""
    return {
        "types": [
            {"id": OutputType.BOOL.value, "name": "BOOL"},
            {"id": OutputType.BYTES.value, "name": "BYTES"},
            {"id": OutputType.UINT256.value, "name": "UINT256"},
            {"id": OutputType.STRING_AND_BOOL.value, "name": "STRING_AND_BOOL"}
        ]
    }

def start_server():
    """Start the FastAPI server"""
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    start_server() 