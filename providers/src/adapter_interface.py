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

        # result = await adapter.process_request(AdapterRequest(
        #     name="Uniswap Pool Data",
        #     network="Base",
        #     description="",
        #     variables="",
        #     category_id=1,
        #     output_type_id=4, # string_and_bool
        #     # prompt="Which pool has the highest TVL and APR?"
        #     prompt="What is the best path to swap amount 1 USDC ( 0x833589fcd6edb6e08f4c7c32d4f71b54bda02913 ) to 1INCH ( 0xc5fecc3a29fb57b5024eec8a2239d4621e111cbe) on BASE?"
        # ))

        # result = await adapter.process_request(AdapterRequest(
        #     name="Uniswap Pool Data",
        #     network="Base",
        #     description="",
        #     variables="",
        #     category_id=1,
        #     output_type_id=4, # string_and_bool
        #     # prompt="Which pool has the highest TVL and APR?"
        #     prompt="Which pool has the highest TVL and APR on BASE?"
        # ))
        
        result = await adapter.process_request(AdapterRequest(
            name="Uniswap Pool Data",
            network="Base",
            description="",
            variables="",
            category_id=1,
            output_type_id=2, # bytes
            prompt="What is the best path to swap amount 1 USDC ( 0x833589fcd6edb6e08f4c7c32d4f71b54bda02913 ) to ZRX ( 0x3bB4445D30AC020a84c1b5A8A2C6248ebC9779D0) on BASE?"
        ))
        print(result)
    finally:
        await adapter.close()

# if __name__ == "__main__":
#     asyncio.run(main())