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
        amount_in: str,
        chain_id: int,
        swapper: str = '0x3fc6DF760D7FC25Ff9c5Cc0D009608ae2f376311'  # Default swapper
    ) -> Dict[str, Any]:
        """
        Get quote from Uniswap API using curl
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount in wei
            chain_id: Chain ID for the tokens
            swapper: Swapper address
            
        Returns:
            Dict containing the quote response
        """
        try:
            # Construct the curl command
            curl_command = [
                'curl',
                'https://api.uniswap.org/v2/quote',
                '-X', 'POST',
                '-H', 'accept: */*',
                '-H', 'accept-language: en-US,en;q=0.9',
                '-H', 'content-type: application/json',
                '-H', 'origin: https://app.uniswap.org',
                '-H', 'referer: https://app.uniswap.org/',
                '-H', 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                '-H', 'x-api-key: JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
                '--data-raw', json.dumps({
                    'amount': amount_in,
                    'tokenIn': token_in,
                    'tokenOut': token_out,
                    'tokenInChainId': chain_id,
                    'tokenOutChainId': chain_id,
                    'type': 'EXACT_INPUT',
                    'configs': [{
                        'routingType': 'CLASSIC',
                        'protocols': ['V3'],
                        'enableUniversalRouter': True,
                        'enableFeeOnTransferFeeFetching': True
                    }]
                })
            ]

            # Execute curl command
            max_retries = 3
            base_delay = 2
            last_error = None

            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        retry_delay = base_delay * (2 ** (attempt - 1))
                        print(f"Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(retry_delay)

                    # Run curl command asynchronously
                    process = await asyncio.create_subprocess_exec(
                        *curl_command,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode != 0:
                        error_msg = stderr.decode().strip()
                        if "429" in error_msg:
                            print(f"Rate limit hit, waiting {base_delay * (2 ** attempt)} seconds...")
                            await asyncio.sleep(base_delay * (2 ** attempt))
                            continue
                        last_error = f"Curl command failed: {error_msg}"
                        if attempt == max_retries - 1:
                            return {
                                "error": "Curl Error",
                                "details": last_error
                            }
                        continue

                    response_data = stdout.decode().strip()
                    
                    # Parse JSON response
                    try:
                        return json.loads(response_data)
                    except json.JSONDecodeError as e:
                        last_error = f"Failed to parse JSON response: {str(e)}, Response: {response_data}"
                        if attempt == max_retries - 1:
                            return {
                                "error": "JSON Parse Error",
                                "details": last_error
                            }
                        continue

                except asyncio.TimeoutError:
                    last_error = "Request timed out"
                    if attempt == max_retries - 1:
                        return {
                            "error": "Timeout",
                            "details": "Request timed out after multiple attempts"
                        }
                    continue
                    
                except Exception as e:
                    last_error = str(e)
                    if attempt == max_retries - 1:
                        return {
                            "error": "Request Failed",
                            "details": last_error
                        }
                    continue

            return {
                "error": "Max retries exceeded",
                "details": last_error or "Failed to get quote after maximum retry attempts"
            }

        except Exception as e:
            return {
                "error": "Unexpected Error",
                "details": str(e)
            }

    async def _handle_swap_path_query(self, query: str, chain_id: int = 8453) -> Dict[str, Any]:
        """
        Handle swap path query and return quote data
        
        Args:
            query: The query string containing swap details
            chain_id: The blockchain chain ID (defaults to 8453 for Base)
            
        Returns:
            Dict[str, Any]: {
                "success": bool,  # Whether the quote was successful
                "data": Dict,     # The complete response data
                "error": str      # Error message if any
            }
        """
        try:
            # Get chain name for prompt from chain_id
            chain_name = next((name for name, info in SUPPORTED_NETWORKS.items() 
                             if info['chain_id'] == chain_id), 'BASE')
            
            # Define prompt template for extracting swap parameters
            swap_template = """
            Extract the following information from the query:
            1. Input token address (format: 0x...)
            2. Output token address (format: 0x...)
            3. Input amount and decimals
            4. Chain/Network (if specified, default to {chain})
            
            Query: {query}

            Consider:
            - Token addresses are 42 characters long starting with '0x'
            - Amount should be converted to wei based on token decimals
            - If decimals are specified, use them for conversion
            - If decimals aren't specified, assume:
              * USDC, USDT, DAI = 6 decimals
              * Most other tokens = 18 decimals
            - If amount is not specified, use default of 1 token
            - Supported networks: {networks}
            - Convert network names to chain IDs:
              {chain_mappings}

            Return in JSON format:
            {{
                "token_in": "address",
                "token_out": "address",
                "amount": "number",
                "decimals": "number",
                "amount_in_wei": "amount converted to wei string",
                "chain_id": "number"
            }}

            Example 1:
            For "1 USDC (0x833... - decimals 6) to 1INCH on Base"
            {{
                "token_in": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
                "token_out": "0xc5fecc3a29fb57b5024eec8a2239d4621e111cbe",
                "amount": 1,
                "decimals": 6,
                "amount_in_wei": "1000000",
                "chain_id": 8453
            }}

            Answer:"""

            # Create chain mappings string for prompt
            chain_mappings = "\n              ".join(
                [f"{name}: {info['chain_id']}" for name, info in SUPPORTED_NETWORKS.items()]
            )

            swap_prompt = PromptTemplate(
                template=swap_template, 
                input_variables=["query", "chain", "networks", "chain_mappings"]
            )
            
            # Create chain and get response
            chain = swap_prompt | self.llm
            response = await chain.ainvoke({
                "query": query,
                "chain": chain_name,
                "networks": ", ".join(SUPPORTED_NETWORKS.keys()),
                "chain_mappings": chain_mappings
            })
            
            # Parse the JSON response
            import json
            try:
                # Clean up markdown formatting from AI response
                content = response.content.strip()
                # Remove markdown code block markers if present
                if content.startswith('```json\n'):
                    content = content[8:]  # Remove ```json\n
                if content.endswith('\n```'):
                    content = content[:-4]  # Remove \n```
                # Remove any remaining ``` markers
                content = content.replace('```', '')
                
                # Parse the cleaned JSON
                params = json.loads(content.strip())
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse AI response: {response.content}")
                print(f"JSON error: {e}")
                raise ValueError("Failed to parse AI response as JSON")
            
            # Validate token addresses
            for key in ['token_in', 'token_out']:
                if not params.get(key) or not Web3.is_address(params[key]):
                    raise ValueError(f"Invalid {key} address: {params.get(key)}")
            
            # Validate chain_id
            detected_chain_id = params.get('chain_id', chain_id)
            if not any(info['chain_id'] == detected_chain_id for info in SUPPORTED_NETWORKS.values()):
                raise ValueError(f"Unsupported chain_id: {detected_chain_id}")
            
            # Use the amount_in_wei directly from AI response
            amount_in = params.get('amount_in_wei', '1000000000000000000')  # Default to 1 token with 18 decimals
            
            # Get quote from Uniswap API
            quote_response = await self._get_quote(
                token_in=params['token_in'],
                token_out=params['token_out'],
                amount_in=amount_in,
                chain_id=detected_chain_id
            )
            
            # Prepare base response with input parameters
            response = {
                "success": False,
                "data": {
                    "request": {
                        "token_in": params['token_in'],
                        "token_out": params['token_out'],
                        "amount": params['amount'],
                        "amount_wei": amount_in,
                        "decimals": params['decimals'],
                        "chain_id": detected_chain_id
                    }
                },
                "error": None
            }
            
            # Check if we have a valid quote response
            if not quote_response:
                response["error"] = "No response from Uniswap API"
                return response
                
            # Add the complete API response
            response["data"]["api_response"] = quote_response
            
            # Check if we have a valid quote with route
            if 'quote' not in quote_response:
                response["error"] = "No quote data in response"
                return response
                
            if ('route' not in quote_response['quote'] or 
                not quote_response['quote']['route'] or 
                not quote_response['quote']['route'][0]):
                response["error"] = f"No valid route found for swap from {params['token_in']} to {params['token_out']} on chain {detected_chain_id}"
                return response
            
            # If we got here, the quote was successful
            response["success"] = True
            
            # Add formatted data for convenience
            response["data"]["response"] = {
                "route": quote_response['quote']['route'],
                "output_amount": quote_response['quote'].get('output', {}).get('amount'),
                "gas_estimate": quote_response['quote'].get('gasUseEstimate', '0'),
                "price_impact": quote_response['quote'].get('priceImpact', 0),
                "route_string": quote_response['quote'].get('routeString', '')
            }
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "data": {
                    "request": {
                        "query": query,
                        "chain_id": chain_id
                    }
                },
                "error": str(e)
            }

    async def _determine_query_type(self, query: str) -> str:
        """
        Use AI to determine the type of query and its intent
        
        Args:
            query: The query string from user
            
        Returns:
            str: The detected query type ('swap_path' or 'pool_info')
        """
        # Define the prompt template for intent detection
        intent_template = """
        Analyze the following query and determine if it's asking about:
        1. Swap path/route information (return 'swap_path')
        2. Pool information/statistics (return 'pool_info')

        Query: {query}

        Consider:
        - Swap queries usually mention: swapping tokens, finding routes, token addresses, best path
        - Pool queries usually mention: liquidity, TVL, volume, fees, pool statistics

        Return only one word - either 'swap_path' or 'pool_info'.

        Answer:"""

        intent_prompt = PromptTemplate(template=intent_template, input_variables=["query"])
        
        try:
            # Create chain and get response
            chain = intent_prompt | self.llm
            response = await chain.ainvoke({
                "query": query
            })
            
            # Clean and validate response
            intent = response.content.strip().lower()
            
            # Validate the response is one of our supported types
            if intent not in ['swap_path', 'pool_info']:
                print(f"AI returned unexpected intent: {intent}, defaulting to pool_info")
                return 'pool_info'
                
            return intent
            
        except Exception as e:
            print(f"Error in intent detection: {e}")
            # Default to pool_info if there's an error
            return 'pool_info'

    async def _format_output(self, raw_response: Dict[str, Any], output_type: OutputType, question: str) -> Union[bool, bytes, int, Tuple[str, bool]]:
        """
        Use AI to format the raw response according to the desired output type and original question
        
        Args:
            raw_response: The raw response from handlers
            output_type: The desired output format
            question: The original user query
            
        Returns:
            Formatted response according to output_type
        """
        format_template = """
        Given the original user question and API response, format the answer according to the specified output type.

        Original Question: {question}

        API Response Data:
        {response}

        Output Type: {output_type}

        Context:
        - The question asks about: {question}
        - We have API data showing: {response}
        - We need to format this as: {output_type}

        Requirements by output type:
        - BOOL: Return "true" or "false" based on whether the API response satisfies the user's query
        - BYTES: Return a hex string (with 0x prefix) representing the encoded path/data
        - UINT256: Return a numeric value that best answers the user's question
        - STRING_AND_BOOL: Return a tuple of (explanation addressing the question, true/false indicating success/validity)

        Consider:
        1. The user's original intent from their question
        2. The relevant data from the API response
        3. The required output format
        4. How to best represent the answer in the required format

        Return in JSON format:
        {{
            "value": "formatted value based on output type",
            "type": "bool|bytes|uint256|tuple",
            "explanation": "brief explanation of why this formatting was chosen"
        }}

        Answer:"""

        try:
            # Create prompt with all required variables
            format_prompt = PromptTemplate(
                template=format_template,
                input_variables=["question", "response", "output_type"]
            )
            
            # Get AI response
            chain = format_prompt | self.llm
            ai_response = await chain.ainvoke({
                "question": question,
                "response": json.dumps(raw_response, indent=2),
                "output_type": output_type.name
            })
            
            # Parse AI response
            content = ai_response.content.strip()
            if content.startswith('```json\n'):
                content = content[8:]
            if content.endswith('\n```'):
                content = content[:-4]
            content = content.replace('```', '')
            
            formatted = json.loads(content.strip())
            
            # Log the explanation for debugging/monitoring
            if 'explanation' in formatted:
                print(f"Format explanation: {formatted['explanation']}")
            
            # Convert to appropriate type
            if output_type == OutputType.BOOL:
                return str(formatted['value']).lower() == 'true'
            elif output_type == OutputType.BYTES:
                return bytes.fromhex(formatted['value'].replace('0x', ''))
            elif output_type == OutputType.UINT256:
                return int(formatted['value'])
            elif output_type == OutputType.STRING_AND_BOOL:
                value = formatted['value']
                if isinstance(value, list) and len(value) == 2:
                    return (str(value[0]), bool(value[1]))
                raise ValueError("Invalid STRING_AND_BOOL format")
            
            raise ValueError(f"Unsupported output type: {output_type}")
            
        except Exception as e:
            print(f"Error formatting output: {e}")
            # Return safe defaults based on output type
            if output_type == OutputType.BOOL:
                return False
            elif output_type == OutputType.BYTES:
                return b''
            elif output_type == OutputType.UINT256:
                return 0
            elif output_type == OutputType.STRING_AND_BOOL:
                return ("Error formatting response", False)
            raise

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
        
        # Get chain_id from network name
        chain_id = SUPPORTED_NETWORKS[network]['chain_id']
        
        try:
            # Determine query type using AI
            query_type = await self._determine_query_type(question)
            
            # Get appropriate handler
            handler = self.api_handlers.get(query_type)
            if not handler:
                raise ValueError(f"No handler found for query type: {query_type}")
            
            # Handle async vs sync handlers
            if asyncio.iscoroutinefunction(handler):
                raw_response = await handler(question, chain_id=chain_id)
            else:
                raw_response = handler(question, chain=network)
            
            # Use AI to format the response according to output_type and original question
            return await self._format_output(raw_response, output_type, question)
            
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
