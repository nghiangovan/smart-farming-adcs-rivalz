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

const fetchTopV3Pools = async (tokenAddress = null) => {
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

fetchTopV3Pools().then(data => console.log(data));
