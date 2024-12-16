import { useContractRead, useContractWrite } from 'wagmi';
import { CONTRACTS } from '../config/contracts';

export function useSmartFarming() {
  // Get user's whitelisted pools
  const { data: whitelistedPools } = useContractRead({
    ...CONTRACTS.SMART_FARMING,
    functionName: 'getUserWhitelistedPools',
  });

  // Add pools to whitelist
  const { writeAsync: addPoolsToWhitelist } = useContractWrite({
    ...CONTRACTS.SMART_FARMING,
    functionName: 'addPoolsToWhitelist',
  });

  // Remove pools from whitelist
  const { writeAsync: removePoolsFromWhitelist } = useContractWrite({
    ...CONTRACTS.SMART_FARMING,
    functionName: 'removePoolsFromWhitelist',
  });

  // Set slippage for swaps
  const { writeAsync: setSlippage } = useContractWrite({
    ...CONTRACTS.SMART_FARMING,
    functionName: 'setSlippageSwap',
  });

  // Request smart farming position
  const { writeAsync: requestSmartFarming } = useContractWrite({
    ...CONTRACTS.SMART_FARMING,
    functionName: 'requestSmartFarming',
  });

  // Add liquidity
  const { writeAsync: addLiquidity } = useContractWrite({
    ...CONTRACTS.SMART_FARMING,
    functionName: 'addLiquidity',
  });

  // Remove liquidity
  const { writeAsync: removeLiquidity } = useContractWrite({
    ...CONTRACTS.SMART_FARMING,
    functionName: 'removeLiquidity',
  });

  return {
    whitelistedPools,
    addPoolsToWhitelist,
    removePoolsFromWhitelist,
    setSlippage,
    requestSmartFarming,
    addLiquidity,
    removeLiquidity,
  };
}
