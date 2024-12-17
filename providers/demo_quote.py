import aiohttp


async def get_uniswap_quote(
    amount_in='1000000000000000000',  # Default 1 token
    token_in='0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48',  # USDC
    token_out='0xade00c28244d5ce17d72e40330b1c318cd12b7c3',  # ADX 
    swapper='0x3fc6DF760D7FC25Ff9c5Cc0D009608ae2f376311'  # Default swapper address
):
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

async def main():
    try:
        quote = await get_uniswap_quote()
        print('Uniswap Quote:', quote)
    except Exception as error:
        print('Failed to get quote:', error)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())