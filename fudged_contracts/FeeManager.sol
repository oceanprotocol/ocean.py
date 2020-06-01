pragma solidity ^0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import './FeeCalculator.sol';
import './FeeCollector.sol';
import './Ownable.sol';

contract FeeManager is FeeCalculator, FeeCollector, Ownable {
    
    constructor()
        public
        Ownable()
    {
    }

    function fooFunction() public pure returns (uint256) {
      return 12;
    }
    
    function withdraw() 
        public
        onlyOwner
    {
        require(
            address(this).balance > 0,
            'FeeManager: Zero balance'
        );
        msg.sender.transfer(address(this).balance);
    }
}
