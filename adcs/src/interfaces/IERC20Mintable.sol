// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../openzeppelin/interfaces/IERC20.sol";

interface IERC20Mintable is IERC20 {
    function mint(address _recipient, uint256 _amount) external;
}
