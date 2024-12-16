// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/mock/SmartFarming.sol";
import "../src/ADCSConsumerBase.sol";
import "../src/openzeppelin/interfaces/IERC20.sol";
import "../src/uniswap/interfaces/IUniswapV3Factory.sol";
import "../src/uniswap/interfaces/IUniswapV3Pool.sol";
import "../src/uniswap/interfaces/INonfungiblePositionManager.sol";

contract SmartFarmingTest is Test {
    SmartFarming public smartFarming;
    address public constant COORDINATOR = address(0x91c5d6e9F50ec656e7094df9fC035924AAA428bb);
    address public constant USDC = address(0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913);
    address public constant WETH = address(0x4200000000000000000000000000000000000006);
    address public constant SWAP_ROUTER02 = address(0x2626664c2603336E57B271c5C0b26F421741e481);
    address public constant FACTORY = address(0x33128a8fC17869897dcE68Ed026d694621f6FDfD);
    address public constant POSITION_MANAGER = address(0x03a520b32C04BF3bEEf7BEb72E919cf822Ed34f1);
    address public constant QUOTER = address(0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a);

    IERC20 public usdcToken = IERC20(USDC);
    address public user = address(0x54C823fa9BEdEC087F3eda8186E29d824D6cFDC2);

    function setUp() public {
        // Fork Base at specific block
        vm.createSelectFork(vm.envString("BASE_PROVIDER"), 23732757);
        vm.label(WETH, "WETH");
        vm.label(USDC, "USDC");
        vm.label(COORDINATOR, "COORDINATOR");
        vm.label(FACTORY, "FACTORY");
        vm.label(POSITION_MANAGER, "POSITION_MANAGER");
        vm.label(QUOTER, "QUOTER");
        vm.label(SWAP_ROUTER02, "SWAP_ROUTER02");
        vm.label(user, "USER");

        // Deploy the SmartFarming contract
        smartFarming = new SmartFarming(COORDINATOR, USDC, SWAP_ROUTER02, FACTORY, POSITION_MANAGER, QUOTER);
        vm.label(address(smartFarming), "SMART_FARMING");

        // Mint USDC to user and approve SmartFarming contract
        vm.startPrank(user);
        deal(USDC, user, 10000 * 1e6); // Assuming USDC has 6 decimals
        usdcToken.approve(address(smartFarming), type(uint256).max);
        console.log("USDC balance of user:", usdcToken.balanceOf(user));
        vm.stopPrank();
    }

    function requestNewFarmingAndFulfillData() public {
        // Set up initial conditions
        uint256 positionTokenId = 0; // Assuming no existing position
        uint256 amount = 1000 * 1e6; // Amount of USDC to add
        bytes memory pathToken0Position; // Empty bytes as we have no position
        bytes memory pathToken1Position; // Empty bytes as we have no position

        // Mock the jobId and callbackGasLimit
        bytes32 jobId = 0x436481cd227a360a61e94dcc948b977fbb38f9cf9e6b31c7394534c0722a1d77; // BASE_data_farming
        uint256 callbackGasLimit = 500_000;

        // User calls requestSmartFarming
        vm.prank(user);
        uint256 requestId = smartFarming.requestSmartFarming(
            jobId, callbackGasLimit, positionTokenId, amount, pathToken0Position, pathToken1Position
        );

        address poolAddress = 0x6c561B446416E1A00E8E93E221854d6eA4171372; // ETH/USDC fee 3000

        IUniswapV3Pool pool = IUniswapV3Pool(poolAddress);
        address token0 = pool.token0();
        address token1 = pool.token1();

        bytes memory pathToken0;
        bytes memory pathToken1;
        if (token0 == USDC) {
            pathToken0 = abi.encodePacked();
            pathToken1 = abi.encodePacked(USDC, uint24(500), token1);
        } else {
            pathToken0 = abi.encodePacked(USDC, uint24(500), token0);
            pathToken1 = abi.encodePacked();
        }

        console.log("-------------------------------------------");
        console.log("- pathToken0 :");
        console.logBytes(pathToken0);
        console.log("- pathToken1 :");
        console.logBytes(pathToken1);
        console.log("-------------------------------------------");

        // Create a mock InfoSuggestPool
        SmartFarming.InfoSuggestPool memory suggestPool = SmartFarming.InfoSuggestPool({
            name: "ETH/USDC",
            addr: poolAddress,
            apr: 1563, // 15.63%
            risk: 5000, // 50.00%
            pathToken0: pathToken0,
            pathToken1: pathToken1
        });

        // Encode the suggestPool as bytes
        bytes memory response = abi.encode(suggestPool);

        // Simulate the coordinator calling fulfillDataRequest
        vm.prank(COORDINATOR);
        smartFarming.rawFulfillDataRequest(requestId, response);
    }   


    function test_RequestNewFarmingAndFulfillData() public {
       requestNewFarmingAndFulfillData();
    }


    // function test_RequestAddMoreFarming() public {
    //     requestNewFarmingAndFulfillData();

    //     // Start Generation Here

    //     // Get the positionManager from the smartFarming contract
    //     INonfungiblePositionManager positionManager = smartFarming.positionManager();

    //     // Get the token ID of the position owned by the deployer
    //     uint256 balance = positionManager.balanceOf(user);
    //     require(balance > 0, "No positions owned by deployer");

    //     uint256 positionTokenId = positionManager.tokenOfOwnerByIndex(user, 0);

    //     // Now you can use positionTokenId for adding more liquidity
    //     uint256 amountMore = 1000 * 10 ** 6; // Amount of USDC to add

    //     // Prepare paths for swapping USDC to token0 and token1
    //     bytes memory pathToken0 = abi.encodePacked(USDC, uint24(500), token0);
    //     bytes memory pathToken1 = abi.encodePacked(USDC, uint24(500), token1);

    //     // Approve USDC transfer to smartFarming contract
    //     vm.startPrank(user);
    //     IERC20(USDC).approve(address(smartFarming), amountMore);

    //     // Call requestAddMoreFarming to add more liquidity
    //     smartFarming.requestAddMoreFarming(positionTokenId, amountMore, poolAddress, pathToken0, pathToken1);
    //     vm.stopPrank();

    // }
}
