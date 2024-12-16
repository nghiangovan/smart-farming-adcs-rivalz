import { http, createConfig } from 'wagmi';
import { base } from 'wagmi/chains';
import { defineChain } from 'viem';

// Contract addresses from test configuration
const CONTRACTS = {
  COORDINATOR: '0x91c5d6e9F50ec656e7094df9fC035924AAA428bb',
  USDC: '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913',
  WETH: '0x4200000000000000000000000000000000000006',
  SWAP_ROUTER02: '0x2626664c2603336E57B271c5C0b26F421741e481',
  FACTORY: '0x33128a8fC17869897dcE68Ed026d694621f6FDfD',
  POSITION_MANAGER: '0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1',
  QUOTER: '0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a',
} as const;

// Base chain configuration
const baseChain = defineChain({
  ...base,
  rpcUrls: {
    default: {
      http: ['https://base.llamarpc.com'],
    },
    public: {
      http: ['https://base.llamarpc.com'],
    },
  },
});

// Wagmi configuration
export const config = createConfig({
  chains: [baseChain],
  transports: {
    [baseChain.id]: http(),
  },
});

export { CONTRACTS };
