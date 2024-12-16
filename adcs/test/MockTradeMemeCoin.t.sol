// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/mock/MockTradeMemeCoin.sol";
import "../src/ADCSConsumerBase.sol";
import "../src/openzeppelin/interfaces/IERC20.sol";
import "../src/uniswap/interfaces/ISwapRouter.sol";

contract MockTradeMemeCoinTest is Test {
    MockTradeMemeCoin public tradeMeme;
    address public constant COORDINATOR = 0x91c5d6e9F50ec656e7094df9fC035924AAA428bb;
    address public constant WETH = 0x4200000000000000000000000000000000000006;
    address public constant ROUTER = 0x2626664c2603336E57B271c5C0b26F421741e481;
    
    // Test memecoin token (using USDC as example)
    address public constant TEST_TOKEN = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    uint8 public constant TEST_TOKEN_DECIMALS = 6;
    
    address public owner;
    uint256 public fork;
    uint256 public BLOCK_NUMBER = 23732757;

    event DataRequested(uint256 indexed requestId);
    event TradeSuccess(uint256 indexed requestId, uint256 amountIn, bool isBuy);
    event MemecoinNotFound(string tokenName);

    function setUp() public {
        // Fork Base at specific block
        fork = vm.createSelectFork(
            vm.envString("BASE_PROVIDER"),
            BLOCK_NUMBER
        );

        // Deploy contract
        owner = address(this);
        tradeMeme = new MockTradeMemeCoin(
            COORDINATOR,
            WETH,
            ROUTER
        );

        // Deal some ETH to test contract
        vm.deal(address(tradeMeme), 10 ether);
        
        // Wrap some ETH to WETH for testing
        (bool success,) = WETH.call{value: 5 ether}("");
        require(success, "Failed to wrap ETH");
        
        // Transfer WETH to trading contract
        IERC20(WETH).transfer(address(tradeMeme), 1 ether);
    }

    function test_AddMemeCoin() public {
        tradeMeme.addMemeCoin("TEST", TEST_TOKEN, TEST_TOKEN_DECIMALS);
        
        (string memory name, address addr, uint8 decimals) = tradeMeme.getMemeCoin(0);
        assertEq(name, "TEST");
        assertEq(addr, TEST_TOKEN);
        assertEq(decimals, TEST_TOKEN_DECIMALS);
    }

    function test_RequestTradeMemeCoin() public {
        bytes32 jobId = bytes32("test-job-id");
        uint256 callbackGasLimit = 500_000;

        vm.expectEmit(true, false, false, false);
        emit DataRequested(1); // First request should have ID 1

        uint256 requestId = tradeMeme.requestTradeMemeCoin(jobId, callbackGasLimit);
        assertEq(requestId, 1);
    }

    function test_TradeMemeCoin_Buy() public {
        // Add test token
        tradeMeme.addMemeCoin("TEST", TEST_TOKEN, TEST_TOKEN_DECIMALS);
        
        // Set reasonable WETH amount for trade
        tradeMeme.setWethAmountForTrade(0.1 ether);
        // Create response data
        ADCSConsumerBase.StringAndBool memory response = ADCSConsumerBase.StringAndBool({
            name: "TEST",
            response: true // true for buy
        });

        // Mock coordinator call
        vm.prank(COORDINATOR);
        vm.expectEmit(true, false, false, true);
        emit TradeSuccess(1, 0.1 ether, true);
        
        tradeMeme.rawFulfillDataRequest(1, response);

        // Verify WETH was spent
        assertLt(
            IERC20(WETH).balanceOf(address(tradeMeme)),
            1 ether,
            "WETH should be spent"
        );
        
        // Verify received test tokens
        assertTrue(
            IERC20(TEST_TOKEN).balanceOf(address(tradeMeme)) > 0,
            "Should have received test tokens"
        );
    }

    function test_TradeMemeCoin_Sell() public {
        // Add test token
        tradeMeme.addMemeCoin("TEST", TEST_TOKEN, TEST_TOKEN_DECIMALS);

        // Deal some test tokens to contract
        deal(TEST_TOKEN, address(tradeMeme), 1000 * 10**TEST_TOKEN_DECIMALS);

        // Create response data
        ADCSConsumerBase.StringAndBool memory response = ADCSConsumerBase.StringAndBool({
            name: "TEST",
            response: false // false for sell
        });

        uint256 initialWethBalance = IERC20(WETH).balanceOf(address(tradeMeme));

        // Mock coordinator call
        vm.prank(COORDINATOR);
        vm.expectEmit(true, false, false, true);
        emit TradeSuccess(1, 100 * 10**TEST_TOKEN_DECIMALS, false);
        
        tradeMeme.rawFulfillDataRequest(1, response);

        // Verify received WETH
        assertTrue(
            IERC20(WETH).balanceOf(address(tradeMeme)) > initialWethBalance,
            "Should have received WETH"
        );
    }

    function test_NonExistentMemeCoin() public {
        // Create response data for non-existent token
        ADCSConsumerBase.StringAndBool memory response = ADCSConsumerBase.StringAndBool({
            name: "NONEXISTENT",
            response: true
        });

        // Mock coordinator call
        vm.prank(COORDINATOR);
        vm.expectEmit(true, false, false, true);
        emit MemecoinNotFound("NONEXISTENT");
        
        tradeMeme.rawFulfillDataRequest(1, response);
    }

    function test_OnlyOwnerFunctions() public {
        address nonOwner = address(0x1);
        
        vm.startPrank(nonOwner);
        
        vm.expectRevert("Ownable: caller is not the owner");
        tradeMeme.addMemeCoin("TEST", TEST_TOKEN, TEST_TOKEN_DECIMALS);
        
        vm.expectRevert("Ownable: caller is not the owner");
        tradeMeme.setWethAmountForTrade(1 ether);
        
        vm.expectRevert("Ownable: caller is not the owner");
        tradeMeme.withdraw();
        
        vm.expectRevert("Ownable: caller is not the owner");
        tradeMeme.withdrawToken(TEST_TOKEN);
        
        vm.stopPrank();
    }

    function test_Withdraw() public {
        uint256 initialBalance = address(owner).balance;
        
        tradeMeme.withdraw();
        
        assertEq(
            address(owner).balance - initialBalance,
            10 ether,
            "Should have withdrawn all ETH"
        );
    }

    function test_WithdrawToken() public {
        // Deal some test tokens
        deal(TEST_TOKEN, address(tradeMeme), 1000 * 10**TEST_TOKEN_DECIMALS);
        
        tradeMeme.withdrawToken(TEST_TOKEN);
        
        assertEq(
            IERC20(TEST_TOKEN).balanceOf(address(tradeMeme)),
            0,
            "Should have withdrawn all tokens"
        );
    }

    receive() external payable {}
}