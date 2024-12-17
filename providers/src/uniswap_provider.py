import requests
import json
from typing import List, Dict, Union, Tuple
import chromadb
from chromadb.utils import embedding_functions
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import os
from dotenv import load_dotenv
from enum import Enum

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

    def handle_adapter_request(self, question: str, output_type: OutputType, network: str) -> Union[bool, bytes, int, Tuple[str, bool]]:
        """Handle requests from adapters with specific output formatting and network"""
        # Normalize network name to match our supported networks
        network = network.upper()
        if network not in SUPPORTED_NETWORKS:
            raise ValueError(f"Unsupported network: {network}")
            
        # Get raw response for specific network
        raw_response = self.query_pools(question, chain=network)
        
        # Format response according to output type
        formatter = self.output_formatters.get(output_type)
        if not formatter:
            raise ValueError(f"Unsupported output type: {output_type}")
            
        return formatter(raw_response)

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
