pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import '@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol';
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";



/**
 * @title Ocean Protocol ERC20 Token Contract
 * @author Ocean Protocol Team
 * @dev Implementation of the Ocean Token.
 */
contract OceanToken is Ownable, ERC20Capped {
    
    using SafeMath for uint256;
    
    uint8 constant DECIMALS = 18;
    uint256 constant CAP = 1410000000;
    uint256 TOTALSUPPLY = CAP.mul(uint256(10) ** DECIMALS);
    
    // keep track token holders
    address[] private accounts = new address[](0);
    mapping(address => bool) private tokenHolders;
    
    /**
     * @dev OceanToken constructor
     * @param contractOwner refers to the owner of the contract
     */
    constructor(
        address contractOwner
    )
    public
    ERC20('Ocean Token', 'OCEAN')
    ERC20Capped(TOTALSUPPLY)
    Ownable()
    {
        transferOwnership(contractOwner);
    }
    
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }
    
    
    /**
     * @dev fallback function
     *      this is a default fallback function in which receives
     *      the collected ether.
     */
    fallback() external payable {revert('Invalid ether transfer');}
    
    /**
     * @dev receive function
     *      this is a default receive function in which receives
     *      the collected ether.
     */
    receive() external payable {revert('Invalid ether transfer');}
    
    
}
