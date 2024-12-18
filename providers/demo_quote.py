import aiohttp
import asyncio

# async def get_uniswap_quote(
#     amount_in='1000000000000000000',  # Default 1 token
#     token_in='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',  # USDC
#     token_out='0xade00c28244d5ce17d72e40330b1c318cd12b7c3',  # ADX 
#     swapper='0x3fc6DF760D7FC25Ff9c5Cc0D009608ae2f376311'  # Default swapper address
# ):
#     max_retries = 3
#     base_delay = 2  # Base delay in seconds
    
#     headers = {
#         'accept': '*/*',
#         'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
#         'content-type': 'application/json',
#         'origin': 'https://app.uniswap.org',
#         'priority': 'u=1, i',
#         'referer': 'https://app.uniswap.org/',
#         'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#         'sec-ch-ua-mobile': '?0',
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'empty',
#         'sec-fetch-mode': 'cors',
#         'sec-fetch-site': 'same-site',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
#         'x-api-key': 'JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
#         'x-app-version': '',
#         'x-request-source': 'uniswap-web',
#         'x-universal-router-version': '1.2',
#     }

#     body = {
#         'amount': amount_in,
#         'gasStrategies': [{
#             'limitInflationFactor': 1.15,
#             'priceInflationFactor': 1.5,
#             'percentileThresholdFor1559Fee': 75,
#             'minPriorityFeeGwei': 2,
#             'maxPriorityFeeGwei': 9,
#         }],
#         'swapper': swapper,
#         'tokenIn': token_in,
#         'tokenInChainId': 1,
#         'tokenOut': token_out,
#         'tokenOutChainId': 1,
#         'type': 'EXACT_INPUT',
#         'urgency': 'normal',
#         'protocols': ['V3'],
#         'autoSlippage': 'DEFAULT',
#     }

#     last_error = None
#     for attempt in range(max_retries):
#         try:
#             # Add delay for retries (exponential backoff)
#             if attempt > 0:
#                 retry_delay = base_delay * (2 ** (attempt - 1))
#                 print(f"Retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})")
#                 await asyncio.sleep(retry_delay)

#             async with aiohttp.ClientSession() as session:
#                 async with session.post(
#                     'https://trading-api-labs.interface.gateway.uniswap.org/v1/quote',
#                     headers=headers,
#                     json=body,
#                     timeout=30
#                 ) as response:
#                     if response.status == 429:
#                         retry_after = int(response.headers.get('Retry-After', base_delay * (2 ** attempt)))
#                         print(f"Rate limit hit, waiting {retry_after} seconds...")
#                         await asyncio.sleep(retry_after)
#                         continue
                        
#                     if not response.ok:
#                         error_text = await response.text()
#                         last_error = f"HTTP error! status: {response.status}, body: {error_text}"
#                         if attempt == max_retries - 1:
#                             raise Exception(last_error)
#                         continue
                        
#                     return await response.json()

#         except Exception as error:
#             last_error = str(error)
#             if attempt == max_retries - 1:
#                 raise Exception(f"Failed after {max_retries} attempts. Last error: {last_error}")
#             continue

#     raise Exception(f"Max retries exceeded. Last error: {last_error}")

# async def main():
#     try:
#         quote = await get_uniswap_quote()
#         print('Uniswap Quote:', quote)
#     except Exception as error:
#         print('Failed to get quote:', error)

# if __name__ == '__main__':
#     asyncio.run(main())


# async def get_uniswap_quote():
#     """
#     Get quote from Uniswap API using aiohttp, similar to the curl request
#     """
#     url = 'https://trading-api-labs.interface.gateway.uniswap.org/v1/quote'
    
#     headers = {
#         'accept': '*/*',
#         'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
#         'content-type': 'application/json',
#         'origin': 'https://app.uniswap.org',
#         'priority': 'u=1, i',
#         'referer': 'https://app.uniswap.org/',
#         'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
#         'sec-ch-ua-mobile': '?0', 
#         'sec-ch-ua-platform': '"Windows"',
#         'sec-fetch-dest': 'empty',
#         'sec-fetch-mode': 'cors',
#         'sec-fetch-site': 'same-site',
#         'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
#         'x-api-key': 'JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
#         'x-app-version': '',
#         'x-request-source': 'uniswap-web',
#         'x-universal-router-version': '1.2'
#     }

#     data = {
#         "amount": "100000000000",
#         "gasStrategies": [{
#             "limitInflationFactor": 1.15,
#             "displayLimitInflationFactor": 1.15,
#             "priceInflationFactor": 1.5,
#             "percentileThresholdFor1559Fee": 75,
#             "minPriorityFeeGwei": 2,
#             "maxPriorityFeeGwei": 9
#         }],
#         "swapper": "0xAAAA44272dc658575Ba38f43C438447dDED45358",
#         "tokenIn": "0x0000000000000000000000000000000000000000",
#         "tokenInChainId": 1,
#         "tokenOut": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", 
#         "tokenOutChainId": 1,
#         "type": "EXACT_OUTPUT",
#         "urgency": "normal",
#         "routingPreference": "CLASSIC"
#     }

#     async with aiohttp.ClientSession() as session:
#         async with session.post(url, headers=headers, json=data) as response:
#             return await response.json()
        
# async def main():
#     try:
#         quote = await get_uniswap_quote()
#         print('Uniswap Quote:', quote)
#     except Exception as error:
#         print('Failed to get quote:', error)

# if __name__ == '__main__':
#     asyncio.run(main())


    
    
import subprocess

def call_uniswap_quote():
    curl_command = [
        'curl',
        'https://trading-api-labs.interface.gateway.uniswap.org/v1/quote',
        '-H', 'accept: */*',
        '-H', 'accept-language: en-US,en;q=0.9,vi;q=0.8',
        '-H', 'content-type: application/json',
        '-H', 'origin: https://app.uniswap.org',
        '-H', 'priority: u=1, i',
        '-H', 'referer: https://app.uniswap.org/',
        '-H', 'sec-ch-ua: "Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        '-H', 'sec-ch-ua-mobile: ?0',
        '-H', 'sec-ch-ua-platform: "Windows"',
        '-H', 'sec-fetch-dest: empty',
        '-H', 'sec-fetch-mode: cors',
        '-H', 'sec-fetch-site: same-site',
        '-H', 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        '-H', 'x-api-key: JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
        '-H', 'x-app-version;',
        '-H', 'x-request-source: uniswap-web',
        '-H', 'x-universal-router-version: 1.2',
        '--data-raw', '{"amount":"100000000000","gasStrategies":[{"limitInflationFactor":1.15,"displayLimitInflationFactor":1.15,"priceInflationFactor":1.5,"percentileThresholdFor1559Fee":75,"minPriorityFeeGwei":2,"maxPriorityFeeGwei":9}],"swapper":"0xAAAA44272dc658575Ba38f43C438447dDED45358","tokenIn":"0x0000000000000000000000000000000000000000","tokenInChainId":1,"tokenOut":"0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48","tokenOutChainId":1,"type":"EXACT_OUTPUT","urgency":"normal","routingPreference":"CLASSIC"}'
    ]
    
    result = subprocess.run(curl_command, capture_output=True, text=True)
    return result.stdout

if __name__ == '__main__':
    print(call_uniswap_quote())
