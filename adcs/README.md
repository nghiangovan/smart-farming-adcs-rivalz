# Docs Smart Farming

## Idea

- I want to use AI agents to analyze Uniswap v3 liquidity data in Base blockchain. From there, find the pool with the best APR and use ADCS as an on-chain AI Oralce to make farming decisions on the pool with the best APR and TVL.

- The data will be mainly concentrated on Uniswap v3 Base blockchain.

- Users simply keep USDC in their wallet and trigger transaction start farming. Let Smart Farming take care of the rest.

## Feature

1. Smart Farming
2. Add more liquidity
3. Remove liquidity
4. Remove liquidity and convert all to USDC

## How to work

### 1. Smart Farming

- Step 1: User approved USDC and trigger `requestSmartFarming` with consumer `SmartFarming` smart contract
- Step 2: `SmartFarming` will create a request to `Coordinator` smart contract
- Step 3: AI agents off-chain will fetch data from Uniswap v3 by Subgraph and analyze data -> suggest best pool farming (base TVL + APR)
- Step 4: AI use Oracle smart contract to update data into `Coordinator` smart contract and trigger fill data for respone of request id
- Step 5: Fill data will trigger decision process farming
- Step 6: In final of `_addLiquidity` function of process farming will transfer position token id of LP back to user

- All setps `SmartFarming` only like a middle contract. It not keep fund of user.

### 2. Increase more liquidity ( simple steps add liquidity into )

### 3. Remove liquidity ( simple steps )

### 4. Remove liquidity and convert all to USDC ( simple steps )

## Smart Farming Flow

### 1. Smart Farming Flow

```mermaid
sequenceDiagram
    participant User
    participant SmartFarming
    participant Coordinator
    participant AI_Agent
    participant Oracle
    participant UniswapV3

    User->>SmartFarming: requestSmartFarming()
    Note over User,SmartFarming: Approve USDC & Position Token
    SmartFarming->>Coordinator: Request Data
    Coordinator-->>AI_Agent: Trigger Analysis
    AI_Agent->>UniswapV3: Fetch Pool Data
    Note over AI_Agent: Analyze TVL + APR
    AI_Agent->>Oracle: Update Best Pool Data
    Oracle->>Coordinator: Fill Data Response
    Coordinator->>SmartFarming: Fulfill Data
    Note over SmartFarming: Process Farming
    alt Has Existing Position
        SmartFarming->>UniswapV3: Remove Old Position
        UniswapV3-->>SmartFarming: Return Tokens
        SmartFarming->>UniswapV3: Swap to USDC
    end
    SmartFarming->>UniswapV3: Swap USDC to Token Pair
    SmartFarming->>UniswapV3: Add Liquidity
    SmartFarming->>User: Transfer Position NFT
```

### 2. Add More Liquidity Flow

```mermaid
sequenceDiagram
    participant User
    participant SmartFarming
    participant UniswapV3

    User->>SmartFarming: addLiquidity()
    Note over User,SmartFarming: Approve USDC & Position Token
    SmartFarming->>UniswapV3: Swap USDC to Token Pair
    SmartFarming->>UniswapV3: Increase Liquidity
    Note over SmartFarming: Position NFT stays with user
```

### 3. Remove Liquidity Flow

```mermaid
sequenceDiagram
    participant User
    participant SmartFarming
    participant UniswapV3

    User->>SmartFarming: removeLiquidity() or removeLiquidityAll()
    Note over User,SmartFarming: Approve Position Token
    SmartFarming->>UniswapV3: Decrease Liquidity
    SmartFarming->>UniswapV3: Collect Tokens
    UniswapV3-->>User: Return Token Pair
```

### 4. Remove Liquidity to USDC Flow

```mermaid
sequenceDiagram
    participant User
    participant SmartFarming
    participant UniswapV3

    User->>SmartFarming: removeLiquidityToUSDC() or removeLiquidityAllToUSDC()
    Note over User,SmartFarming: Approve Position Token
    SmartFarming->>UniswapV3: Decrease Liquidity
    SmartFarming->>UniswapV3: Collect Tokens
    SmartFarming->>UniswapV3: Swap Token Pair to USDC
    SmartFarming->>User: Return USDC
```

## Run test

```
forge test --match-contract SmartFarmingTest --match-test test_RequestNewFarmingAndFulfillData -vvvv
```
