import asyncio
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
import os
from dotenv import load_dotenv

# Load environment variables from .env file in the providers directory
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path=dotenv_path)

class UniswapDataProvider:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.vectorstore = None
        self.uniswap_graphql_url = 'https://interface.gateway.uniswap.org/v1/graphql'
        self.headers = {
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
            'user-agent':
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        self.query = '''
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
        '''
        self.variables = {
            'chain': 'BASE',
            'first': 100,
            'cursor': None,
            'tokenAddress': None,
        }

    async def fetch_uniswap_data(self):
        transport = AIOHTTPTransport(url=self.uniswap_graphql_url, headers=self.headers)
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql(self.query)
        async with client:
            result = await client.execute_async(query, variable_values=self.variables)
            return result['topV3Pools']

    async def update_data(self):
        while True:
            print("Fetching latest Uniswap v3 data...")
            pools = await self.fetch_uniswap_data()
            documents = []
            for pool in pools:
                content = (
                    f"Pool ID: {pool['id']}, "
                    f"Tokens: {pool['token0']['symbol']}/{pool['token1']['symbol']}, "
                    f"Fee Tier: {pool['feeTier']}, "
                    f"Volume USD: {pool['volumeUSD']}, "
                    f"TVL USD: {pool['totalValueLockedUSD']}"
                )
                documents.append(Document(page_content=content))

            print("Updating vector store with new data...")
            self.vectorstore = FAISS.from_documents(documents, self.embeddings)
            print("Data updated.")
            # Wait before fetching new data (e.g., 10 minutes)
            await asyncio.sleep(600)

    async def handle_request(self, query_text: str):
        if self.vectorstore is None:
            print("Vector store is not initialized yet.")
            return "Data is still loading. Please try again later."

        retriever = self.vectorstore.as_retriever()

        # Use OpenRouter's API
        openrouter_api_key = os.environ.get('OPENROUTER_API_KEY')
        if not openrouter_api_key:
            return "OPENROUTER_API_KEY is not set. Please set it in your environment or .env file."

        llm = ChatOpenAI(
            temperature=0,
            openai_api_key=openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            model_name="gpt-3.5-turbo",
        )

        qa = RetrievalQA(retriever=retriever, llm=llm)
        response = qa.run(query_text)
        return response

async def main():
    provider = UniswapDataProvider()

    pools = await provider.fetch_uniswap_data()
    print(pools)
    
    # asyncio.create_task(provider.update_data())

    while True:
        query = input("Enter your query: ")
        response = await provider.handle_request(query)
        print("Response:", response)

if __name__ == '__main__':
    asyncio.run(main()) 