import asyncio
import json
import os
from enum import Enum
from typing import Any, Dict, List, Tuple, Union

import aiohttp
import chromadb
import requests
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from web3 import Web3

# Define the query for fetching top V3 pools
TOP_V3_POOLS_QUERY = {
    "operationName": "TopV3Pools",
    "variables": {
        "chain": "BASE",
        "first": 100,
        "cursor": None,
        "tokenAddress": None,
    },
    "query": """
        query TopV3Pools($chain: Chain!, $first: Int!, $cursor: Float, $tokenAddress: String) {
            topV3Pools(first: $first, chain: $chain, tokenFilter: $tokenAddress, tvlCursor: $cursor) {
                id
                protocolVersion
                address
                totalLiquidity {
                    value
                }
                feeTier
                token0 {
                    id
                    symbol
                    name
                    address
                    chain
                    __typename
                }
                token1 {
                    id
                    symbol
                    name
                    address
                    chain
                    __typename
                }
                txCount
                volume24h: cumulativeVolume(duration: DAY) {
                    value
                }
                volume30d: cumulativeVolume(duration: MONTH) {
                    value
                }
            }
        }
    """
}

SUPPORTED_NETWORKS = {
    'BASE': {'chain_id': 8453, 'name': 'Base'},
    'ARBITRUM': {'chain_id': 42161, 'name': 'Arbitrum'},
    'RIVALZ': {'chain_id': 1234, 'name': 'Rivalz'}  # Replace with actual chain ID
}

# Function to fetch top V3 pools TVL
def fetch_top_v3_pools_tvl(chain='BASE', token_address=None):
    try:
        if chain not in SUPPORTED_NETWORKS:
            raise ValueError(f"Unsupported chain: {chain}")
            
        # Update variables with chain and tokenAddress
        variables = TOP_V3_POOLS_QUERY["variables"].copy()
        variables["chain"] = chain
        if token_address:
            variables["tokenAddress"] = token_address
        
        # Prepare the GraphQL payload
        payload = {
            "operationName": TOP_V3_POOLS_QUERY["operationName"],
            "variables": variables,
            "query": TOP_V3_POOLS_QUERY["query"],
        }
        
        # Set request headers
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,vi;q=0.8",
            "content-type": "application/json",
            "origin": "https://app.uniswap.org",
            "referer": "https://app.uniswap.org/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        # Send the POST request to the Uniswap endpoint
        url = "https://interface.gateway.uniswap.org/v1/graphql"
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an error for bad HTTP responses
        
        # Return the JSON response
        return response.json()
    except Exception as error:
        print(f"Error fetching top V3 pools: {error}")
        raise

class OutputType(Enum):
    BOOL = 1
    BYTES = 2
    UINT256 = 3
    STRING_AND_BOOL = 4

# Add new constants for API endpoints
UNISWAP_QUOTE_API = "https://trading-api-labs.interface.gateway.uniswap.org/v1/quote"
UNISWAP_API_KEY = os.getenv('UNISWAP_API_KEY')

# Add new class for swap path handling
class SwapPathHandler:
    @staticmethod
    def encode_path(path_data: List[Dict]) -> bytes:
        """Encode swap path into bytes format"""
        encoded = b''
        for hop in path_data:
            # Encode token address (20 bytes)
            encoded += Web3.to_bytes(hexstr=hop['tokenIn']['address'])
            # Encode fee (3 bytes)
            encoded += int(hop['fee']).to_bytes(3, 'big')
        # Add final token address
        if path_data:
            encoded += Web3.to_bytes(hexstr=path_data[-1]['tokenOut']['address'])
        return encoded

class UniswapPoolAgent:
    def __init__(self):
        load_dotenv()
        
        # Initialize ChromaDB
        self.chroma_client = chromadb.Client()
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Create collections for each supported network
        self.collections = {}
        for network in SUPPORTED_NETWORKS:
            self.collections[network] = self.chroma_client.get_or_create_collection(
                name=f"uniswap_pools_{network.lower()}",
                embedding_function=self.embedding_function
            )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name="openai/gpt-4o-mini",
            openai_api_key=os.getenv('OPENROUTER_API_KEY'),
            openai_api_base=os.getenv('OPENROUTER_API_BASE'),
            temperature=0.7,
        )
        
        # Define RAG prompt template
        self.template = """
        Given the following Uniswap pool data and the question, provide a detailed answer:
        
        Context: {context}
        
        Question: {question}
        
        Answer: Let's analyze this step by step:"""
        
        self.prompt = PromptTemplate(template=self.template, input_variables=["context", "question"])
        
        # Add output type mapping
        self.output_formatters = {
            OutputType.BOOL: self._format_bool_output,
            OutputType.BYTES: self._format_bytes_output,
            OutputType.UINT256: self._format_uint256_output,
            OutputType.STRING_AND_BOOL: self._format_string_bool_output
        }
        
        # Initialize other attributes
        self.web3 = Web3()
        self.session = None  # Will be initialized in async context
        
        # Add API handlers mapping
        self.api_handlers = {
            'swap_path': self._handle_swap_path_query,
            'pool_info': self.query_pools,  # existing handler
            # Add more API handlers here
        }

    def process_pool_data(self, pools_data: List[Dict], chain: str) -> None:
        """Process and store pool data in the vector database"""
        if chain not in SUPPORTED_NETWORKS:
            raise ValueError(f"Unsupported chain: {chain}")
            
        documents = []
        metadatas = []
        ids = []
        
        network_info = SUPPORTED_NETWORKS[chain]
        
        for pool in pools_data:
            # Create a readable description of the pool
            pool_description = (
                f"Pool {pool['address']} between {pool['token0']['symbol']}-{pool['token1']['symbol']} "
                f"with {pool['totalLiquidity']['value']:.2f} TVL, "
                f"24h volume: {pool['volume24h']['value']:.2f}, "
                f"30d volume: {pool['volume30d']['value']:.2f}, "
                f"fee tier: {pool['feeTier']}, "
                f"on {network_info['name']} network (chain ID: {network_info['chain_id']})"
            )
            
            documents.append(pool_description)
            metadatas.append({
                "address": pool['address'],
                "token0": pool['token0']['symbol'],
                "token1": pool['token1']['symbol'],
                "tvl": pool['totalLiquidity']['value'],
                "chain_id": network_info['chain_id'],
                "chain_name": network_info['name']
            })
            ids.append(pool['address'])
        
        # Add to network-specific ChromaDB collection
        self.collections[chain].add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

    def query_pools(self, question: str, chain: str, n_results: int = 3) -> str:
        """Query the vector database and get AI response for specific chain"""
        if chain not in SUPPORTED_NETWORKS:
            raise ValueError(f"Unsupported chain: {chain}")
            
        # Search for relevant pools in the chain-specific collection
        results = self.collections[chain].query(
            query_texts=[question],
            n_results=n_results
        )
        
        # Combine context
        context = "\n".join(results['documents'][0])
        
        # Create chain and get response
        chain = self.prompt | self.llm
        response = chain.invoke({
            "context": context,
            "question": question
        })
        
        return response.content

    def update_pool_data(self):
        """Fetch latest pool data and update the database for all supported networks"""
        try:
            success = True
            for chain in SUPPORTED_NETWORKS:
                try:
                    # Fetch new data for each chain
                    data = fetch_top_v3_pools_tvl(chain=chain)
                    pools = data['data']['topV3Pools']
                    
                    # Process and store new data
                    self.process_pool_data(pools, chain)
                except Exception as e:
                    print(f"Error updating pool data for {chain}: {e}")
                    success = False
            return success
        except Exception as e:
            print(f"Error in update_pool_data: {e}")
            return False

    def _format_bool_output(self, response: str) -> bool:
        """Format response as boolean"""
        # Simple sentiment analysis - can be made more sophisticated
        positive_keywords = ['yes', 'true', 'high', 'good', 'above']
        return any(keyword in response.lower() for keyword in positive_keywords)

    def _format_bytes_output(self, response: str) -> bytes:
        """Format response as bytes"""
        return response.encode('utf-8')

    def _format_uint256_output(self, response: str) -> int:
        """Format response as uint256"""
        # Extract first number from response
        import re
        numbers = re.findall(r'\d+\.?\d*', response)
        if numbers:
            return int(float(numbers[0]))
        return 0

    def _format_string_bool_output(self, response: str) -> Tuple[str, bool]:
        """Format response as string and bool tuple"""
        is_positive = self._format_bool_output(response)
        return (response, is_positive)
    
    async def _get_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: str = '1000000000000000000',  # Default 1 token
        chain_id: int = 1,  # Default to Ethereum mainnet
        swapper: str = '0x3fc6DF760D7FC25Ff9c5Cc0D009608ae2f376311'  # Default swapper
    ) -> Dict[str, Any]:
        """
        Get quote from Uniswap API
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount in wei (default: 1 token)
            chain_id: Chain ID for the tokens (default: 1 for Ethereum)
            swapper: Swapper address (default: Universal Router)
            
        Returns:
            Dict containing the quote response
        """
        try:
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
                'content-type': 'application/json',
                'origin': 'https://app.uniswap.org',
                'priority': 'u=1, i',
                'referer': 'https://app.uniswap.org/',
                'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'x-api-key': 'JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
                'x-app-version': '',
                'x-request-source': 'uniswap-web',
                'x-universal-router-version': '1.2',
            }

            body = {
                'amount': amount_in,
                'gasStrategies': [{
                    'limitInflationFactor': 1.15,
                    'priceInflationFactor': 1.5,
                    'percentileThresholdFor1559Fee': 75,
                    'minPriorityFeeGwei': 2,
                    'maxPriorityFeeGwei': 9,
                }],
                'swapper': swapper,
                'tokenIn': token_in,
                'tokenInChainId': 1,
                'tokenOut': token_out,
                'tokenOutChainId': 1,
                'type': 'EXACT_INPUT',
                'urgency': 'normal',
                'protocols': ['UNISWAPX_V2', 'V3', 'V2'],
                'autoSlippage': 'DEFAULT',
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    'https://trading-api-labs.interface.gateway.uniswap.org/v1/quote',
                    headers=headers,
                    json=body
                ) as response:
                    if not response.ok:
                        raise Exception(f'HTTP error! status: {response.status}')
                    return await response.json()

        except Exception as error:
            print('Error fetching Uniswap quote:', str(error))
            raise

    async def _handle_swap_path_query(self, query: str) -> bytes:
        """Handle swap path query and return encoded path"""
        try:
            # Extract token addresses from query using regex or NLP
            import re
            token_addresses = re.findall(r'0x[a-fA-F0-9]{40}', query)
            if len(token_addresses) < 2:
                raise ValueError("Could not find both token addresses in query")
            
            token_in, token_out = token_addresses[:2]
            
            # Get quote from Uniswap API
            quote_response = await self._get_quote(
                token_in=token_in,
                token_out=token_out,
                amount_in="1000000000000000000",  # 1 token
                chain_id=8453  # Base chain ID
            )
            
            # Add error handling for quote response
            if not quote_response or 'quote' not in quote_response:
                print(f"Unexpected API response: {quote_response}")
                return b''
            
            if 'route' not in quote_response['quote'] or not quote_response['quote']['route']:
                print("No route found in quote response")
                return b''
            
            # Extract and encode path
            path_data = quote_response['quote']['route'][0]
            return SwapPathHandler.encode_path(path_data)
            
        except Exception as e:
            print(f"Error in _handle_swap_path_query: {e}")
            return b''

    def _determine_query_type(self, query: str) -> str:
        """Determine the type of query using simple keyword matching"""
        if any(keyword in query.lower() for keyword in ['swap', 'path', 'route']):
            return 'swap_path'
        return 'pool_info'

    async def handle_request(self, question: str, output_type: OutputType, network: str = 'BASE') -> Union[bool, bytes, int, Tuple[str, bool]]:
        """
        Unified request handler that processes both API and vector DB queries
        
        Args:
            question: The query string
            output_type: The desired output format (BOOL, BYTES, etc.)
            network: The blockchain network to query (defaults to BASE)
        
        Returns:
            bool: For BOOL output type
            bytes: For BYTES output type
            int: For UINT256 output type
            Tuple[str, bool]: For STRING_AND_BOOL output type
        """
        # Normalize network name and validate
        network = network.upper()
        if network not in SUPPORTED_NETWORKS:
            raise ValueError(f"Unsupported network: {network}")
        
        try:
            # Determine query type using NLP or pattern matching
            query_type = self._determine_query_type(question)
            
            # Get appropriate handler
            handler = self.api_handlers.get(query_type)
            if not handler:
                raise ValueError(f"No handler found for query type: {query_type}")
            
            # Handle async vs sync handlers
            if asyncio.iscoroutinefunction(handler):
                raw_response = await handler(question)
            else:
                # For vector DB queries, pass the network parameter
                raw_response = handler(question, chain=network)
            
            # Format response according to output type
            if output_type == OutputType.BOOL:
                return self._format_bool_output(raw_response)
            elif output_type == OutputType.BYTES:
                if isinstance(raw_response, bytes):
                    return raw_response
                return self._format_bytes_output(raw_response)
            elif output_type == OutputType.UINT256:
                return self._format_uint256_output(raw_response)
            elif output_type == OutputType.STRING_AND_BOOL:
                return self._format_string_bool_output(raw_response)
            else:
                raise ValueError(f"Unsupported output type: {output_type}")
            
        except Exception as e:
            print(f"Error processing request: {e}")
            # Return appropriate default values based on output type
            if output_type == OutputType.BOOL:
                return False
            elif output_type == OutputType.BYTES:
                return b''
            elif output_type == OutputType.UINT256:
                return 0
            elif output_type == OutputType.STRING_AND_BOOL:
                return ("Error processing request", False)
            raise

    async def close(self):
        """Close the API client session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def __del__(self):
        """Cleanup when object is destroyed"""
        if hasattr(self, 'session') and self.session and not self.session.closed:
            asyncio.create_task(self.close())

    async def initialize(self):
        """Initialize async components"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self

# # Example usage
# if __name__ == "__main__":
#     try:
#         # Initialize agent
#         agent = UniswapPoolAgent()
        
#         # Update pool data
#         agent.update_pool_data()
        
#         # Example queries
#         questions = [
#             "Which pool has the highest TVL?",
#             "What are the most active USDC pairs?",
#             "What is the average fee tier for high volume pools?"
#         ]
        
#         for question in questions:
#             print(f"\nQuestion: {question}")
#             response = agent.query_pools(question)
#             print(f"Response: {response}")
            
#     except Exception as e:
#         print(f"An error occurred: {e}")
