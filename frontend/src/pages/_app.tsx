import { ChakraProvider } from '@chakra-ui/react';
import { createWeb3Modal } from '@web3modal/wagmi/react';
import { WagmiProvider } from 'wagmi';
import { config } from '../config/wagmi';

createWeb3Modal({
  wagmiConfig: config,
  projectId: process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || '',
  chains: config.chains,
});

export default function App({ Component, pageProps }) {
  return (
    <WagmiProvider config={config}>
      <ChakraProvider>
        <Component {...pageProps} />
      </ChakraProvider>
    </WagmiProvider>
  );
}
