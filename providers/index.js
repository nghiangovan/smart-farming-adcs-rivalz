const fetchUniswapStats = async (chainId = 'ALL_NETWORKS') => {
  try {
    // Construct a URL to fetch Uniswap exploration statistics for a specific blockchain network
    const url =
      `https://interface.gateway.uniswap.org/v2/uniswap.explore.v1.ExploreStatsService/ExploreStats` +
      `?connect=v1` +
      `&encoding=json` +
      `&message=${encodeURIComponent(JSON.stringify({ chainId }))}`;
    console.log('Fetching URL:', url);
    const response = await fetch(url, {
      headers: {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
        'origin': 'https://app.uniswap.org',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'referer': 'https://app.uniswap.org/',
        'user-agent':
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
      },
      method: 'GET',
    });

    return await response.json();
  } catch (error) {
    console.error('Error fetching Uniswap stats:', error);
    throw error;
  }
};

// // Example usage
// fetchUniswapStats().then(data => console.log(data));

const topV3PoolsQuery = {
  operationName: 'TopV3Pools',
  variables: {
    chain: 'BASE',
    first: 100,
    cursor: null,
    tokenAddress: null,
  },
  query: `query TopV3Pools($chain: Chain!, $first: Int!, $cursor: Float, $tokenAddress: String) {
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
  }`,
};

const fetchTopV3PoolsTVL = async (tokenAddress = null) => {
  try {
    const queryVariables = {
      ...topV3PoolsQuery.variables,
      ...(tokenAddress && { tokenAddress }),
    };

    const response = await fetch('https://interface.gateway.uniswap.org/v1/graphql', {
      method: 'POST',
      headers: {
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
      },
      body: JSON.stringify({
        ...topV3PoolsQuery,
        variables: queryVariables,
      }),
    });

    return await response.json();
  } catch (error) {
    console.error('Error fetching top V3 pools:', error);
    throw error;
  }
};

fetchTopV3PoolsTVL().then(data => console.log(data));

// async function getUniswapQuote({
//   amountIn = '1000000000000000000', // Default 1 token
//   tokenIn = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48', // USDC
//   tokenOut = '0xade00c28244d5ce17d72e40330b1c318cd12b7c3', // ADX
//   swapper = '0x3fc6DF760D7FC25Ff9c5Cc0D009608ae2f376311', // Default swapper address
// } = {}) {
//   try {
//     const response = await fetch('https://trading-api-labs.interface.gateway.uniswap.org/v1/quote', {
//       method: 'POST',
//       headers: {
//         'accept': '*/*',
//         'accept-language': 'en-US,en;q=0.9,vi;q=0.8',
//         'content-type': 'application/json',
//         'origin': 'https://app.uniswap.org',
//         'priority': 'u=1, i',
//         'referer': 'https://app.uniswap.org/',
//         'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
//         'sec-ch-ua-mobile': '?0',
//         'sec-ch-ua-platform': '"Windows"',
//         'sec-fetch-dest': 'empty',
//         'sec-fetch-mode': 'cors',
//         'sec-fetch-site': 'same-site',
//         'user-agent':
//           'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
//         'x-api-key': 'JoyCGj29tT4pymvhaGciK4r1aIPvqW6W53xT1fwo',
//         'x-app-version': '',
//         'x-request-source': 'uniswap-web',
//         'x-universal-router-version': '1.2',
//       },
//       body: JSON.stringify({
//         amount: amountIn,
//         gasStrategies: [
//           {
//             limitInflationFactor: 1.15,
//             priceInflationFactor: 1.5,
//             percentileThresholdFor1559Fee: 75,
//             minPriorityFeeGwei: 2,
//             maxPriorityFeeGwei: 9,
//           },
//         ],
//         swapper: swapper,
//         tokenIn: tokenIn,
//         tokenInChainId: 1,
//         tokenOut: tokenOut,
//         tokenOutChainId: 1,
//         type: 'EXACT_INPUT',
//         urgency: 'normal',
//         protocols: ['UNISWAPX_V2', 'V3', 'V2'],
//         autoSlippage: 'DEFAULT',
//       }),
//     });

//     if (!response.ok) {
//       throw new Error(`HTTP error! status: ${response.status}`);
//     }

//     return await response.json();
//   } catch (error) {
//     console.error('Error fetching Uniswap quote:', error.message);
//     throw error;
//   }
// }

// // Example usage
// async function main() {
//   try {
//     const quote = await getUniswapQuote();
//     console.log('Uniswap Quote:', quote);
//   } catch (error) {
//     console.error('Failed to get quote:', error);
//   }
// }

// main();

// {
//   "requestId": "0f5cbfc6-db42-41c8-807b-5ac2547c8f73",
//   "routing": "CLASSIC",
//   "quote": {
//       "chainId": 1,
//       "input": {
//           "amount": "1000000",
//           "token": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
//       },
//       "output": {
//           "amount": "3964457611274009993",
//           "token": "0xade00c28244d5ce17d72e40330b1c318cd12b7c3",
//           "recipient": "0x3fc6DF760D7FC25Ff9c5Cc0D009608ae2f376311"
//       },
//       "swapper": "0x3fc6DF760D7FC25Ff9c5Cc0D009608ae2f376311",
//       "route": [
//           [
//               {
//                   "type": "v3-pool",
//                   "address": "0x3416cF6C708Da44DB2624D63ea0AAef7113527C6",
//                   "tokenIn": {
//                       "chainId": 1,
//                       "decimals": "6",
//                       "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
//                       "symbol": "USDC"
//                   },
//                   "tokenOut": {
//                       "chainId": 1,
//                       "decimals": "6",
//                       "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
//                       "symbol": "USDT"
//                   },
//                   "fee": "100",
//                   "liquidity": "38992420561072046",
//                   "sqrtRatioX96": "79237341052854002555301505352",
//                   "tickCurrent": "2",
//                   "amountIn": "1000000"
//               },
//               {
//                   "type": "v3-pool",
//                   "address": "0x8de5977111C68C3fE95E63e7F7319dD5a01F77a0",
//                   "tokenIn": {
//                       "chainId": 1,
//                       "decimals": "6",
//                       "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
//                       "symbol": "USDT"
//                   },
//                   "tokenOut": {
//                       "chainId": 1,
//                       "decimals": "18",
//                       "address": "0xADE00C28244d5CE17D72E40330B1c318cD12B7c3",
//                       "symbol": "ADX"
//                   },
//                   "fee": "3000",
//                   "liquidity": "590317399939246516",
//                   "sqrtRatioX96": "39734051875043337155476",
//                   "tickCurrent": "-290128",
//                   "amountOut": "3954546467245824968"
//               }
//           ]
//       ],
//       "slippage": 0.5,
//       "tradeType": "EXACT_INPUT",
//       "quoteId": "db06b2c6-d944-49de-b83c-fff42820b6e8",
//       "gasFeeUSD": "4.328918376746040768",
//       "gasFeeQuote": "9453684734736707773",
//       "gasUseEstimate": "162000",
//       "priceImpact": 0.56,
//       "txFailureReasons": [],
//       "maxPriorityFeePerGas": "2000000000",
//       "maxFeePerGas": "9362584327",
//       "gasFee": "1124665619940000",
//       "gasEstimates": [
//           {
//               "type": "eip1559",
//               "strategy": {
//                   "limitInflationFactor": 1.15,
//                   "priceInflationFactor": 1.5,
//                   "percentileThresholdFor1559Fee": 75,
//                   "minPriorityFeeGwei": 2,
//                   "maxPriorityFeeGwei": 9
//               },
//               "gasLimit": "186300",
//               "gasFee": "1744249460120100",
//               "maxFeePerGas": "9362584327",
//               "maxPriorityFeePerGas": "2000000000"
//           }
//       ],
//       "routeString": "[V3] 100.00% = USDC -- 0.01% [0x3416cF6C708Da44DB2624D63ea0AAef7113527C6]USDT -- 0.3% [0x8de5977111C68C3fE95E63e7F7319dD5a01F77a0]ADX",
//       "blockNumber": "21406521",
//       "portionAmount": "9911144028185024",
//       "portionBips": 25,
//       "portionRecipient": "0x000000fee13a103A10D593b9AE06b3e05F2E7E1c"
//   },
//   "permitData": {
//       "domain": {
//           "name": "Permit2",
//           "chainId": 1,
//           "verifyingContract": "0x000000000022D473030F116dDEE9F6B43aC78BA3"
//       },
//       "types": {
//           "PermitSingle": [
//               {
//                   "name": "details",
//                   "type": "PermitDetails"
//               },
//               {
//                   "name": "spender",
//                   "type": "address"
//               },
//               {
//                   "name": "sigDeadline",
//                   "type": "uint256"
//               }
//           ],
//           "PermitDetails": [
//               {
//                   "name": "token",
//                   "type": "address"
//               },
//               {
//                   "name": "amount",
//                   "type": "uint160"
//               },
//               {
//                   "name": "expiration",
//                   "type": "uint48"
//               },
//               {
//                   "name": "nonce",
//                   "type": "uint48"
//               }
//           ]
//       },
//       "values": {
//           "details": {
//               "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
//               "amount": "1461501637330902918203684832716283019655932542975",
//               "expiration": "1736840815",
//               "nonce": "0"
//           },
//           "spender": "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD",
//           "sigDeadline": "1734250615"
//       }
//   }
// }
