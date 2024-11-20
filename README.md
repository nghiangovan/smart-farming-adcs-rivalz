ADCS - AI/Data Oracle System
The Agentic Data Coordination System (ADCS) is an **example project** that demonstrates how to build an AI agent capable of automatically trading memecoins. This project serves as a connectivity module and represents the next evolution in data infrastructure tailored specifically for AI Agents. Designed to revolutionize the future of Artificial Intelligence, ADCS builds an expansive data network that emphasizes rapid validation and ultra-low latency.

## ADCS Folder Functionality

The `adcs` folder contains the core smart contracts and related code for the ADCS system. It includes:

- **Smart Contracts**: Solidity contracts that define the core functionalities of the ADCS network, located in the `src` directory.
- **Deployment Scripts**: Hardhat deployment scripts in the `deploy` directory, used to deploy contracts to various networks.
- **Libraries**: Custom libraries such as `ADCS.sol`, `Buffer.sol`, and `CBOR.sol` in the `libraries` directory, which provide utilities for data encoding and decoding.
- **Interfaces**: Interface definitions in the `interfaces` directory for interacting with external contracts.
- **Scripts**: Helper scripts in the `scripts` directory for tasks like migrations and utilities.
- **Configuration Files**: Configuration files like `hardhat.config.ts`, `.eslintrc`, `.prettierrc`, and `package.json` for setting up the development environment.
- **Type Definitions**: Generated TypeScript typings in the `typechain` directory, facilitating type-safe contract interactions.
- **Tests**: Test scripts located in the `test` directory to ensure the contracts function as expected.
- **Migration Data**: Migration JSON files in the `migration` directory, detailing deployment configurations for different networks.

## Core Contracts Explanation

### MockTradeMemeCoin.sol

Located at `adcs/src/mock/MockTradeMemeCoin.sol`, this is the main contract of the ADCS system. It implements an AI agent that automatically trades memecoins based on data fetched from the ADCS network.

**Key Features:**

- **Automated Trading:** Executes trades of memecoins on Uniswap V3 based on signals received from the AI agent.
- **Data Requests:** Uses the ADCS network to request data that determines whether to buy or sell a memecoin.
- **Memecoin Management:** Allows adding new memecoins to trade and manages a list of available memecoins.
- **Integration with Uniswap V3:** Utilizes Uniswap V3's `ISwapRouter` for executing trades.

**Main Functions:**

- `requestTradeMemeCoin`: Initiates a data request to the ADCS network.
- `fulfillDataRequest`: Called by the ADCS coordinator to fulfill the data request and trigger a trade.
- `tradeMemeCoin`: Executes the buy or sell trade on Uniswap V3 based on the data received.
- `addMemeCoin`: Adds a new memecoin to the list of tradable tokens.
- `setWethAmountForTrade`: Sets the amount of WETH to use for trading.

### ADCSConsumerBase.sol

An abstract contract that serves as the base for consumer contracts interacting with the ADCS coordinator. It initializes data requests and verifies the fulfillment.

### ADCSConsumerFulfill.sol

Defines abstract contracts for fulfilling data requests of different data types. `MockTradeMemeCoin.sol` extends `ADCSConsumerFulfillStringAndBool` to handle responses containing a string (memecoin name) and a boolean (buy/sell signal).

### Interfaces and Libraries

- **Interfaces (`interfaces` directory):** Define the necessary interfaces for interacting with the ADCS coordinator and token contracts.
- **Libraries (`libraries` directory):** Include utility libraries like `ADCS.sol` for building data requests and `Buffer.sol` for handling dynamic byte buffers.

## Deployment Guide

Follow these steps to deploy the `MockTradeMemeCoin.sol` contract:

### Prerequisites

- **Node.js and NPM**: Ensure you have Node.js and npm installed.
- **Hardhat**: This project uses Hardhat for compiling and deploying contracts.
- **Environment Variables**: Create an `.env` file based on `.env.example` with your deployment configurations.

### Steps

1. **Install Dependencies**

   Navigate to the `adcs` directory and install the required npm packages:
   ```bash
   cd adcs
   npm install   ```

2. **Configure Environment Variables**

   Create a `.env` file in the `adcs` directory by copying `.env.example`:
   ```bash
   cp .env.example .env   ```

   Fill in the necessary environment variables in the `.env` file:
   ```ini
   TESTNET_DEPLOYER=your_private_key
   RIVALZ_TESTNET_PROVIDER=your_provider_url
   EXPLORER_API_KEY=your_explorer_api_key
   ARBITRUM_PROVIDER=your_arbitrum_provider_url
   ARBITRUM_API_KEY=your_arbitrum_api_key
   BASE_API_KEY=your_base_api_key
   BASE_PROVIDER=your_base_provider_url   ```

3. **Compile Contracts**

   Compile the smart contracts using Hardhat:
   ```bash
   npx hardhat compile   ```

4. **Set Deployment Configuration**

   Ensure that the deployment script `adcs/deploy/memeTrade/deploy.ts` is properly configured with the network and contract addresses. Check the migration JSON files in `adcs/migration/{network}/tradeMeme/` and update them if necessary.

5. **Deploy the Contract**

   Deploy `MockTradeMemeCoin.sol` to your desired network using Hardhat:
   ```bash
   npx hardhat deploy --network your_network_name --tags MockTradeMemeCoin   ```

   Replace `your_network_name` with the target network specified in `hardhat.config.ts` (e.g., `arbitrum`, `base`, `hardhat`).

6. **Verify Deployment**

   After deployment, you can verify the contract on the block explorer (if supported):
   ```bash
   npx hardhat verify --network your_network_name deployed_contract_address constructor_arguments   ```

   Replace `deployed_contract_address` with the address of the deployed contract and `constructor_arguments` with any arguments passed to the constructor.

7. **Interact with the Contract**

   - **Add Memecoins**: Use the `addMemeCoin` function to add memecoins that the contract can trade.
     ```typescript
     await mockTradeMemeCoin.addMemeCoin("MEME", "0xMemecoinAddress", 18);     ```

   - **Request Trade**: Initiate a trade request using `requestTradeMemeCoin` by providing the appropriate `jobId` and `callbackGasLimit`.
     ```typescript
     const requestId = await mockTradeMemeCoin.requestTradeMemeCoin(jobId, gasLimit);     ```

   - **Fulfill Data Request**: The ADCS coordinator will fulfill the data request by calling `fulfillDataRequest`, triggering the trade.

8. **Fund the Contract**

   Ensure the contract has enough WETH for trading:

   - **Wrap ETH to WETH**: Send ETH to the WETH contract to receive WETH.
   - **Transfer WETH to Contract**: Transfer the required amount of WETH to the `MockTradeMemeCoin` contract.

9. **Test the Trading Functionality**

   Verify that the contract can successfully trade memecoins by simulating data fulfillment or interacting with the ADCS network to provide real data.

## Additional Information

For more detailed information about the contracts and their functionalities, refer to the comments within each contract file in the `src` directory. If you encounter any issues during deployment or execution, ensure that all dependencies are correctly installed and that your environment variables are properly configured.

