pragma solidity ^0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import './SafeMath.sol';

contract FeeCalculator {

    using SafeMath for uint256;
    uint256 constant private BASE_TX_COST = 44000;
    uint256 constant private BASE = 10;
    
    function calculateRange(
        uint256 number
    ) 
        public
        pure
        returns(uint256)
    {
        uint256 remainder = number;
        uint256 zeros = 0;
        for(uint256 i = 0 ; remainder >= BASE; i++){
            remainder = remainder.div(BASE);
            zeros += 1;
        }
        return zeros;
    }
			      
    function calculateFee(
        uint256 num_tokens_minted,
        uint256 cap
    )
        public
        pure
        returns (uint256)
    {
      uint256 fee_in_wei = 10;
      return fee_in_wei;
        /* require( */
        /*     cap >= num_tokens_minted, */
        /*     'FeeCalculator: Invalid cap' */
        /* ); */
        
        /* uint256 tokensRange = calculateRange(num_tokens_minted); */
        /* uint256 tokensRangeToll = tokensRange.mul(BASE_TX_COST); */
        /* return tokensRangeToll.div( */
        /*         calculateRange(cap) */
        /*     ).div(BASE); */
    }
}
