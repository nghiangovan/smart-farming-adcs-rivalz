import { useState } from 'react';
import { useSmartFarming } from '@/hooks/useSmartFarming';
import { Box, Button, Input, VStack, Text, useToast } from '@chakra-ui/react';

export function PoolWhitelist() {
  const [poolAddress, setPoolAddress] = useState('');
  const toast = useToast();
  const { whitelistedPools, addPoolsToWhitelist, removePoolsFromWhitelist } = useSmartFarming();

  const handleAddPool = async () => {
    try {
      await addPoolsToWhitelist([poolAddress]);
      toast({
        title: 'Pool added to whitelist',
        status: 'success',
      });
    } catch (error) {
      toast({
        title: 'Failed to add pool',
        status: 'error',
      });
    }
  };

  return (
    <Box>
      <Text fontSize='xl' mb={4}>
        Pool Whitelist
      </Text>

      <VStack spacing={4}>
        <Input placeholder='Pool Address' value={poolAddress} onChange={e => setPoolAddress(e.target.value)} />

        <Button onClick={handleAddPool}>Add Pool to Whitelist</Button>

        <Text>Whitelisted Pools:</Text>
        {whitelistedPools?.map((pool: string) => (
          <Text key={pool}>{pool}</Text>
        ))}
      </VStack>
    </Box>
  );
}
