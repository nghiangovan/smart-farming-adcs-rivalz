// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../ADCSConsumerFulfill.sol";
import "../openzeppelin/Ownable.sol";
import "../uniswap/interfaces/ISwapRouter02.sol";
import "../uniswap/interfaces/IQuoterV2.sol";
import "../uniswap/interfaces/INonfungiblePositionManager.sol";
import "../uniswap/interfaces/IUniswapV3Factory.sol";
import "../uniswap/interfaces/IUniswapV3Pool.sol";
import "../uniswap/interfaces/IV3SwapRouter.sol";
import "../openzeppelin/interfaces/IERC20.sol";
import "../openzeppelin/SafeERC20.sol";
import "../openzeppelin/utils/ReentrancyGuard.sol";

contract SmartFarming is ADCSConsumerFulfillBytes, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    int24 internal constant MIN_TICK = -887272;
    int24 internal constant MAX_TICK = -MIN_TICK;

    address public USDC;
    ISwapRouter02 public swapRouter02;
    INonfungiblePositionManager public positionManager;
    IUniswapV3Factory public factory;
    IQuoterV2 public quoterV2;

    struct InfoRequest {
        address user;
        uint256 positionTokenId;
        uint256 amount;
        bytes pathToken0Position; // path swap from token0 of position to USDC
        bytes pathToken1Position; // path swap from token1 of position to USDC
    }

    struct InfoSuggestPool {
        string name;
        address addr;
        uint16 apr; // 10000 = 100.00%
        uint16 risk; // 10000 = 100.00%
        bytes pathToken0; // path swap from USDC to token0
        bytes pathToken1; // path swap from USDC to token1
    }

    mapping(address => uint256) public userSlippageSwap; // user => slippage (from 1.00 to 100.00)
    mapping(address => mapping(address => bool)) public mapUserWhitelistPools;
    mapping(address => address[]) public arrayUserWhitelistPools;
    mapping(uint256 => InfoRequest) public requestIdUser; // requestId => InfoRequest()

    address[] public usersFarming;

    // Events
    event Deposited(address indexed user, uint256 amount);
    event Withdrawn(address indexed user, uint256 amount);
    event FarmingStarted(address indexed user, address indexed pool);
    event FarmingStopped(address indexed user, address indexed pool);
    event AddedPoolsToWhitelist(address indexed user, address[] indexed pools);
    event RemovedPoolsFromWhitelist(address indexed user, address[] indexed pools);
    event LiquidityAddedMore(address indexed user, address indexed pool, uint256 amount);

    // Errors
    error InsufficientBalance(string code, uint256 amount);
    error InsufficientAllowance(string code, uint256 amount);
    error PoolNotInWhitelist();
    error OwnerNotApprovedForThisContract();
    error NotOwnerPosition();

    constructor(
        address _coordinator,
        address _usdc,
        address _swapRouter,
        address _factory,
        address _positionManager,
        address _quoterV2
    ) ADCSConsumerBase(_coordinator) Ownable(msg.sender) {
        USDC = _usdc;
        swapRouter02 = ISwapRouter02(_swapRouter);
        factory = IUniswapV3Factory(_factory);
        positionManager = INonfungiblePositionManager(_positionManager);
        quoterV2 = IQuoterV2(_quoterV2);
        IERC20(USDC).approve(address(swapRouter02), type(uint256).max);
    }

    function changeConfig(
        address _usdc,
        address _swapRouter02,
        address _factory,
        address _positionManager,
        address _quoterV2
    ) external onlyOwner {
        if (_usdc != address(0)) USDC = _usdc;
        if (_swapRouter02 != address(0)) swapRouter02 = ISwapRouter02(_swapRouter02);
        if (_factory != address(0)) factory = IUniswapV3Factory(_factory);
        if (_positionManager != address(0)) positionManager = INonfungiblePositionManager(_positionManager);
        if (_quoterV2 != address(0)) quoterV2 = IQuoterV2(_quoterV2);
    }

    function setSlippageSwap(uint256 _slippage) external {
        userSlippageSwap[msg.sender] = _slippage;
    }

    // Add multiple pools to user's whitelist
    function addPoolsToWhitelist(address[] calldata pools) external {
        for (uint256 i = 0; i < pools.length; i++) {
            address pool = pools[i];
            if (mapUserWhitelistPools[msg.sender][pool]) continue;
            mapUserWhitelistPools[msg.sender][pool] = true;
            arrayUserWhitelistPools[msg.sender].push(pool);
        }
        emit AddedPoolsToWhitelist(msg.sender, pools);
    }

    // Remove multiple pools from user's whitelist
    function removePoolsFromWhitelist(address[] calldata pools) external {
        for (uint256 i = 0; i < pools.length; i++) {
            address pool = pools[i];
            if (!mapUserWhitelistPools[msg.sender][pool]) continue;
            mapUserWhitelistPools[msg.sender][pool] = false;
            address[] storage whitelistArray = arrayUserWhitelistPools[msg.sender];
            for (uint256 j = 0; j < whitelistArray.length; j++) {
                if (whitelistArray[j] == pool) {
                    whitelistArray[j] = whitelistArray[whitelistArray.length - 1];
                    whitelistArray.pop();
                    break;
                }
            }
        }
        emit RemovedPoolsFromWhitelist(msg.sender, pools);
    }

    // Get user's whitelisted pools
    function getUserWhitelistedPools() external view returns (address[] memory) {
        return arrayUserWhitelistPools[msg.sender];
    }

    // Request and process farming pool data
    function requestSmartFarming(
        bytes32 jobId,
        uint256 callbackGasLimit,
        uint256 positionTokenId,
        uint256 amount, // amount of USDC to add
        bytes memory pathToken0Position, // path swap from token0 of position to USDC
        bytes memory pathToken1Position // path swap from token1 of position to USDC
    ) external returns (uint256 requestId) {
        if (positionTokenId != 0 && positionManager.getApproved(positionTokenId) != address(this)) {
            revert OwnerNotApprovedForThisContract();
        }

        bytes32 typeId = keccak256(abi.encodePacked("bytes"));
        ADCS.Request memory req = buildRequest(jobId, typeId);
        requestId = COORDINATOR.requestData(callbackGasLimit, req);
        requestIdUser[requestId] = InfoRequest({
            user: msg.sender,
            positionTokenId: positionTokenId,
            amount: amount,
            pathToken0Position: pathToken0Position,
            pathToken1Position: pathToken1Position
        });
        return requestId;
    }

    function getInfoRequest(uint256 requestId) external view returns (InfoRequest memory) {
        return requestIdUser[requestId];
    }

    // Fulfill farming pool request
    function fulfillDataRequest(uint256 requestId, bytes memory response) internal virtual override {
        InfoSuggestPool memory suggestPool = abi.decode(response, (InfoSuggestPool));
        _processFarming(requestIdUser[requestId], suggestPool);
    }

    // Process suggested farming pools with whitelist check
    function _processFarming(InfoRequest memory ir, InfoSuggestPool memory suggestPool) internal {
        // Check if whitelist not empty and pool not in the user's whitelist
        if (arrayUserWhitelistPools[ir.user].length > 0 && !mapUserWhitelistPools[ir.user][suggestPool.addr]) {
            revert PoolNotInWhitelist();
        }

        // If whitelist is empty then passed all pools

        uint256 totalAmountOut = 0;
        uint256 positionTokenId = ir.positionTokenId;

        if (ir.positionTokenId != 0) {
            (,, address token0, address token1, uint24 fee,,, uint128 liquidity,,,,) =
                positionManager.positions(ir.positionTokenId);
            address addrPoolPosition = factory.getPool(token0, token1, fee);

            if (suggestPool.addr != addrPoolPosition) {
                totalAmountOut = _removeLiquidityToUSDC(
                    ir.positionTokenId,
                    liquidity,
                    ir.pathToken0Position,
                    ir.pathToken1Position,
                    address(this)
                );
                positionTokenId = 0;
            }
        }

        _addLiquidity(
            ir.user,
            suggestPool.addr,
            totalAmountOut,
            ir.amount,
            positionTokenId,
            suggestPool.pathToken0,
            suggestPool.pathToken1
        );
    }

    function addLiquidity(
        uint256 positionTokenId,
        uint256 amountMore,
        address poolAddress,
        bytes memory pathToken0,
        bytes memory pathToken1
    ) external {
        _addLiquidity(msg.sender, poolAddress, 0, amountMore, positionTokenId, pathToken0, pathToken1);
    }

    // Add liquidity to a specific pool
    function _addLiquidity(
        address user,
        address poolAddress,
        uint256 amountHeld, // amount of USDC held if have remove liquidity
        uint256 amountMore, // amount of USDC need transfer more
        uint256 positionTokenId,
        bytes memory pathToken0, // path swap from USDC to token0
        bytes memory pathToken1 // path swap from USDC to token1
    ) internal {
        if (positionTokenId != 0 && positionManager.getApproved(positionTokenId) != address(this)) {
            revert OwnerNotApprovedForThisContract();
        }

        if (IERC20(USDC).balanceOf(user) < amountMore) revert InsufficientBalance("USDC", amountMore);
        if (IERC20(USDC).allowance(user, address(this)) < amountMore) revert InsufficientAllowance("USDC", amountMore);
        if (amountMore > 0) IERC20(USDC).safeTransferFrom(user, address(this), amountMore);

        IUniswapV3Pool pool = IUniswapV3Pool(poolAddress);
        address token0 = pool.token0();
        address token1 = pool.token1();
        uint24 fee = pool.fee();

        uint256 amount = amountHeld + amountMore;

        uint256 halfAmount = amount / 2;
        uint256 amount0;
        uint256 amount1;

        if (token0 == USDC) amount0 = halfAmount;
        else amount0 = swapExactInput(pathToken0, halfAmount);

        if (token1 == USDC) amount1 = halfAmount;
        else amount1 = swapExactInput(pathToken1, halfAmount);

        if (IERC20(token0).allowance(address(this), address(positionManager)) < amount0) {
            IERC20(token0).approve(address(positionManager), type(uint256).max);
        }

        if (IERC20(token1).allowance(address(this), address(positionManager)) < amount1) {
            IERC20(token1).approve(address(positionManager), type(uint256).max);
        }

        if (positionTokenId == 0) {
            (, int24 currentTick,,,,,) = pool.slot0();
            int24 tickSpacing = pool.tickSpacing();
            int24 tickLower = currentTick - (currentTick % tickSpacing) - (tickSpacing * 6); // 6% below current price
            int24 tickUpper = MAX_TICK - (MAX_TICK % tickSpacing); // Upper limit to max tick

            // Ensure ticks are valid
            if (tickLower < MIN_TICK) tickLower = MIN_TICK;
            if (tickUpper > MAX_TICK) tickUpper = MAX_TICK;

            INonfungiblePositionManager.MintParams memory params = INonfungiblePositionManager.MintParams({
                token0: token0,
                token1: token1,
                fee: fee,
                tickLower: tickLower,
                tickUpper: tickUpper,
                amount0Desired: amount0,
                amount1Desired: amount1,
                amount0Min: 0,
                amount1Min: 0,
                recipient: address(this),
                deadline: block.timestamp + 15 minutes
            });

            (uint256 tokenId,,,) = positionManager.mint(params);
            positionManager.safeTransferFrom(address(this), user, tokenId);

            emit FarmingStarted(msg.sender, poolAddress);
        } else {
            INonfungiblePositionManager.IncreaseLiquidityParams memory params = INonfungiblePositionManager
                .IncreaseLiquidityParams({
                tokenId: positionTokenId,
                amount0Desired: amount0,
                amount1Desired: amount1,
                amount0Min: 0,
                amount1Min: 0,
                deadline: block.timestamp + 15 minutes
            });

            positionManager.increaseLiquidity(params);

            emit LiquidityAddedMore(user, poolAddress, amount);
        }
    }

    function swapExactInput(bytes memory path, uint256 amountIn) internal returns (uint256 amountOut) {
        // 400 = 4.00% is Default if slippage is not set
        uint256 slippage = userSlippageSwap[msg.sender] == 0 ? 400 : userSlippageSwap[msg.sender];
        (uint256 estimatedAmountOut,,,) = quoterV2.quoteExactInput(path, amountIn);
        uint256 amountOutMinimum = (estimatedAmountOut * (10000 - slippage)) / 10000;
        IV3SwapRouter.ExactInputParams memory params = IV3SwapRouter.ExactInputParams({
            path: path,
            recipient: address(this),
            amountIn: amountIn,
            amountOutMinimum: amountOutMinimum
        });
        amountOut = swapRouter02.exactInput(params);
    }

    function removeLiquidity(uint256 positionTokenId, uint128 amountLiquidity) external {
        _removeLiquidity(positionTokenId, amountLiquidity);
    }

    function removeLiquidityAll(uint256 positionTokenId) external {
        (,,,,,,, uint128 liquidity,,,,) = positionManager.positions(positionTokenId);
        _removeLiquidity(positionTokenId, liquidity);
    }

    function removeLiquidityToUSDC(
        uint256 positionTokenId,
        uint128 amountLiquidity,
        bytes memory pathToken0,
        bytes memory pathToken1
    ) external {
        _removeLiquidityToUSDC(
            positionTokenId, amountLiquidity, pathToken0, pathToken1, positionManager.ownerOf(positionTokenId)
        );
    }

    function removeLiquidityAllToUSDC(uint256 positionTokenId, bytes memory pathToken0, bytes memory pathToken1)
        external
    {
        (,,,,,,, uint128 liquidity,,,,) = positionManager.positions(positionTokenId);
        _removeLiquidityToUSDC(
            positionTokenId, liquidity, pathToken0, pathToken1, positionManager.ownerOf(positionTokenId)
        );
    }

    // Remove liquidity from current farming pool
    function _removeLiquidity(uint256 positionTokenId, uint128 amountLiquidity) internal {
        if (positionManager.ownerOf(positionTokenId) != msg.sender) revert NotOwnerPosition();
        address user = positionManager.ownerOf(positionTokenId);

        if (positionTokenId != 0 && positionManager.getApproved(positionTokenId) != address(this)) {
            revert OwnerNotApprovedForThisContract();
        }

        // Decrease liquidity
        INonfungiblePositionManager.DecreaseLiquidityParams memory params = INonfungiblePositionManager
            .DecreaseLiquidityParams({
            tokenId: positionTokenId,
            liquidity: amountLiquidity,
            amount0Min: 0,
            amount1Min: 0,
            deadline: block.timestamp + 15 minutes
        });

        positionManager.decreaseLiquidity(params);

        // Collect tokens
        INonfungiblePositionManager.CollectParams memory collectParams = INonfungiblePositionManager.CollectParams({
            tokenId: positionTokenId,
            recipient: user,
            amount0Max: type(uint128).max,
            amount1Max: type(uint128).max
        });

        positionManager.collect(collectParams);
    }

    // Remove liquidity from current farming pool
    function _removeLiquidityToUSDC(
        uint256 positionTokenId,
        uint128 amountLiquidity,
        bytes memory pathToken0, // path swap from token0 to USDC
        bytes memory pathToken1, // path swap from token1 to USDC
        address to // address to receive USDC
    ) internal returns (uint256 totalAmountOut) {
        if (positionManager.ownerOf(positionTokenId) != msg.sender) revert NotOwnerPosition();
        if (positionTokenId != 0 && positionManager.getApproved(positionTokenId) != address(this)) {
            revert OwnerNotApprovedForThisContract();
        }

        // Decrease liquidity
        INonfungiblePositionManager.DecreaseLiquidityParams memory params = INonfungiblePositionManager
            .DecreaseLiquidityParams({
            tokenId: positionTokenId,
            liquidity: amountLiquidity,
            amount0Min: 0,
            amount1Min: 0,
            deadline: block.timestamp + 15 minutes
        });

        positionManager.decreaseLiquidity(params);

        (,, address token0, address token1,,,,,,, uint128 tokensOwed0, uint128 tokensOwed1) =
            positionManager.positions(positionTokenId);

        // Collect tokens
        INonfungiblePositionManager.CollectParams memory collectParams = INonfungiblePositionManager.CollectParams({
            tokenId: positionTokenId,
            recipient: address(this),
            amount0Max: type(uint128).max,
            amount1Max: type(uint128).max
        });

        positionManager.collect(collectParams);

        if (IERC20(token0).allowance(address(this), address(swapRouter02)) < tokensOwed0) {
            IERC20(token0).approve(address(swapRouter02), type(uint256).max);
        }

        if (IERC20(token1).allowance(address(this), address(swapRouter02)) < tokensOwed1) {
            IERC20(token1).approve(address(swapRouter02), type(uint256).max);
        }

        uint256 amountOut0 = token0 != address(USDC) ? swapExactInput(pathToken0, tokensOwed0) : tokensOwed0;
        uint256 amountOut1 = token1 != address(USDC) ? swapExactInput(pathToken1, tokensOwed1) : tokensOwed1;

        totalAmountOut = amountOut0 + amountOut1;

        if (to != address(this)) IERC20(USDC).safeTransfer(to, totalAmountOut);
    }

    function withdrawAssets(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) payable(owner()).transfer(amount);
        else IERC20(token).safeTransfer(owner(), amount);
    }

    function withdrawAllAssets(address token) external onlyOwner {
        if (token == address(0)) payable(owner()).transfer(address(this).balance);
        else IERC20(token).safeTransfer(owner(), IERC20(token).balanceOf(address(this)));
    }

    receive() external payable {}
}
