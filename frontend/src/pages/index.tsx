import { ConnectButton } from '@/components/ConnectButton';
import { PoolWhitelist } from '@/components/PoolWhitelist';
import { FarmingPosition } from '@/components/FarmingPosition';
import { Box, Container, VStack } from '@chakra-ui/react';

export default function Home() {
  return (
    <Container maxW='container.lg' py={8}>
      <VStack spacing={8} align='stretch'>
        <Box display='flex' justifyContent='flex-end'>
          <ConnectButton />
        </Box>

        <PoolWhitelist />
        <FarmingPosition />
      </VStack>
    </Container>
  );
}
