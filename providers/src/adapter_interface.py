from typing import Any, NamedTuple
import asyncio

from uniswap_provider import OutputType, UniswapPoolAgent


class AdapterRequest(NamedTuple):
    name: str
    network: str
    description: str
    variables: str
    category_id: int
    output_type_id: int
    prompt: str

class AdapterInterface:
    def __init__(self):
        self.agent = None
        
    async def initialize(self):
        """Initialize the adapter with async components"""
        if self.agent is None:
            self.agent = await UniswapPoolAgent().initialize()
        return self

    async def close(self):
        """Cleanup resources"""
        if self.agent:
            await self.agent.close()

    def process_request(self, request: AdapterRequest) -> Any:
        """Process incoming adapter requests"""
        # Convert output_type_id to OutputType enum
        output_type = OutputType(request.output_type_id)
        
        # Process the request through the UniswapPoolAgent
        result = self.agent.handle_request(
            question=request.prompt,
            output_type=output_type,
            network=request.network
        )
        
        return result

    def update_data(self) -> bool:
        """Update the provider's data"""
        return self.agent.update_pool_data() 

async def main():
    adapter = await AdapterInterface().initialize()
    try:
        result = await adapter.process_request(AdapterRequest(
            name="Uniswap Pool Data",
            network="Base",
            description="Get the latest pool data from Uniswap",
            variables="",
            category_id=1,
            output_type_id=2,
            # prompt="Which pool has the highest TVL and APR?"
            prompt="What is the best path to swap amount 100 USDC ( 0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48 ) to ADX ( 0xade00c28244d5ce17d72e40330b1c318cd12b7c3 )?"
        ))
        print(result)
    finally:
        await adapter.close()

if __name__ == "__main__":
    asyncio.run(main())