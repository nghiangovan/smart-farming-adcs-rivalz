import smartFarmingABI from './ABIs/SmartFarming.json';
import ERC20ABI from './ABIs/ERC20.json';

export const CONTRACTS = {
  SMART_FARMING: {
    address: process.env.NEXT_PUBLIC_SMART_FARMING_ADDRESS || '',
    abi: smartFarmingABI.abi,
  },
  USDC: {
    address: process.env.NEXT_PUBLIC_USDC_ADDRESS || '',
    abi: ERC20ABI.abi,
  },
} as const;
