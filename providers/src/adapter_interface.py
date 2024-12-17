from typing import Any, NamedTuple

from .uniswap_provider import OutputType, UniswapPoolAgent


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
        self.agent = UniswapPoolAgent()
        
    def process_request(self, request: AdapterRequest) -> Any:
        """Process incoming adapter requests"""
        # Convert output_type_id to OutputType enum
        output_type = OutputType(request.output_type_id)
        
        # Process the request through the UniswapPoolAgent
        result = self.agent.handle_adapter_request(
            question=request.prompt,
            output_type=output_type,
            network=request.network
        )
        
        return result

    def update_data(self) -> bool:
        """Update the provider's data"""
        return self.agent.update_pool_data() 