// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.

// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.

// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

pragma solidity 0.8.12;
// Copyright Balancer, BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import './BNum.sol';


import "../../interfaces/IFactoryRouter.sol";

contract BMath is BConst, BNum {

   // uint public _swapMarketFee;
    uint public _swapPublishMarketFee;
    uint internal _swapFee;
  
    address public router; // BFactory address to push token exitFee to

    address internal _datatokenAddress; //datatoken address
    address internal _baseTokenAddress; //base token address
    mapping(address => uint) public communityFees;

     mapping(address => uint) public publishMarketFees;
   // mapping(address => uint) public marketFees;


    function getOPCFee() public view returns (uint) {
        return IFactoryRouter(router).getOPCFee(_baseTokenAddress);
    }
    
    struct swapfees{
        uint256 LPFee;
        uint256 oceanFeeAmount;
        uint256 publishMarketFeeAmount;
        uint256 consumeMarketFee;
    }
    /**********************************************************************************************
    // calcSpotPrice                                                                             //
    // sP = spotPrice                                                                            //
    // bI = tokenBalanceIn                ( bI / wI )         1                                  //
    // bO = tokenBalanceOut         sP =  -----------  *  ----------                             //
    // wI = tokenWeightIn                 ( bO / wO )     ( 1 - sF )                             //
    // wO = tokenWeightOut                                                                       //
    // sF = swapFee                                                                              //
    **********************************************************************************************/
    function calcSpotPrice(
        uint tokenBalanceIn,
        uint tokenWeightIn,
        uint tokenBalanceOut,
        uint tokenWeightOut,
        uint _swapMarketFee
    )
        internal view
        returns (uint spotPrice)
        
    {   
       

        uint numer = bdiv(tokenBalanceIn, tokenWeightIn);
        uint denom = bdiv(tokenBalanceOut, tokenWeightOut);
        uint ratio = bdiv(numer, denom);
        uint scale = bdiv(BONE, bsub(BONE, _swapFee+getOPCFee()+_swapPublishMarketFee+_swapMarketFee));
      
        return  (spotPrice = bmul(ratio, scale));
    }

    
    //    data = [
    //         inRecord.balance,
    //         inRecord.denorm,
    //         outRecord.balance,
    //         outRecord.denorm
    //     ];
    function calcOutGivenIn(
        uint[4] memory data,
        uint tokenAmountIn,
        //address tokenInAddress,
        uint256 _consumeMarketSwapFee

    )
        public view
        returns (uint tokenAmountOut, uint balanceInToAdd, swapfees memory _swapfees)
    {
        uint weightRatio = bdiv(data[1], data[3]);

        _swapfees.oceanFeeAmount =  bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, getOPCFee())));

        
        _swapfees.publishMarketFeeAmount =  bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, _swapPublishMarketFee)));
        

        _swapfees.LPFee = bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, _swapFee)));
        _swapfees.consumeMarketFee = bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, _consumeMarketSwapFee)));
        uint totalFee =_swapFee+getOPCFee()+_swapPublishMarketFee+_consumeMarketSwapFee;

        uint adjustedIn = bsub(BONE, totalFee);
        
        adjustedIn = bmul(tokenAmountIn, adjustedIn);
         
        uint y = bdiv(data[0], badd(data[0], adjustedIn));
        uint foo = bpow(y, weightRatio);
        uint bar = bsub(BONE, foo);
        

        tokenAmountOut = bmul(data[2], bar);
       
        return (tokenAmountOut, bsub(tokenAmountIn,(_swapfees.oceanFeeAmount+_swapfees.publishMarketFeeAmount+_swapfees.consumeMarketFee)), _swapfees);
        
    }

     
    function calcInGivenOut(
        uint[4] memory data,
        uint tokenAmountOut,
        uint _consumeMarketSwapFee
    )
        public view 
        returns (uint tokenAmountIn, uint tokenAmountInBalance, swapfees memory _swapfees)
    {
        uint weightRatio = bdiv(data[3], data[1]);
        uint diff = bsub(data[2], tokenAmountOut);
        uint y = bdiv(data[2], diff);
        uint foo = bpow(y, weightRatio);
        foo = bsub(foo, BONE);
        uint totalFee =_swapFee+getOPCFee()+_consumeMarketSwapFee+_swapPublishMarketFee;
        
        
        tokenAmountIn = bdiv(bmul(data[0], foo), bsub(BONE, totalFee));
        _swapfees.oceanFeeAmount =  bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, getOPCFee())));
        
     
        _swapfees.publishMarketFeeAmount =  bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, _swapPublishMarketFee)));

     
        _swapfees.LPFee = bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, _swapFee)));
        _swapfees.consumeMarketFee = bsub(tokenAmountIn, bmul(tokenAmountIn, bsub(BONE, _consumeMarketSwapFee)));
        
      
        tokenAmountInBalance = bsub(tokenAmountIn,(_swapfees.oceanFeeAmount+_swapfees.publishMarketFeeAmount+_swapfees.consumeMarketFee));
      
        
        return (tokenAmountIn, tokenAmountInBalance,_swapfees);
    }

    function calcPoolOutGivenSingleIn(
        uint tokenBalanceIn,
        uint poolSupply,
        uint tokenAmountIn
       
    )
        internal pure
        returns (uint poolAmountOut)
    {
        uint tokenAmountInAfterFee = bmul(tokenAmountIn, BONE);
        uint newTokenBalanceIn = badd(tokenBalanceIn, tokenAmountInAfterFee);
        uint tokenInRatio = bdiv(newTokenBalanceIn, tokenBalanceIn);
        uint poolRatio = bsub(tokenInRatio,BONE);
        uint newPoolSupply = bmul(poolRatio, poolSupply);
        require(newPoolSupply >= 2, 'ERR_TOKEN_AMOUNT_IN_TOO_LOW'); 
        newPoolSupply = newPoolSupply/2;
        return newPoolSupply;
    }

    function calcSingleInGivenPoolOut(
        uint tokenBalanceIn,
        uint poolSupply,
        uint poolAmountOut
    )
        internal pure
        returns (uint tokenAmountIn)
    {
        uint newPoolSupply = badd(poolSupply, poolAmountOut);
        uint poolRatio = bdiv(newPoolSupply, poolSupply);
        uint tokenInRatio = bsub(poolRatio, BONE);
        uint newTokenBalanceIn = bmul(tokenInRatio, tokenBalanceIn);
        require(newTokenBalanceIn >= 1, 'ERR_POOL_AMOUNT_OUT_TOO_LOW'); 
        newTokenBalanceIn = newTokenBalanceIn * 2;
        return newTokenBalanceIn;
    }

    function calcSingleOutGivenPoolIn(
        uint tokenSupply,
        uint poolSupply,
        uint poolAmountIn
    )
        internal pure
        returns (uint tokenAmountOut)
    {
        require(poolAmountIn >= 1, 'ERR_POOL_AMOUNT_IN_TOO_LOW'); 
        poolAmountIn = poolAmountIn * 2;
        uint newPoolSupply = bsub(poolSupply, poolAmountIn);
        uint poolRatio = bdiv(newPoolSupply, poolSupply);
        uint tokenOutRatio = bsub(BONE,poolRatio);
        uint newTokenBalanceOut = bmul(tokenOutRatio, tokenSupply);
        return newTokenBalanceOut;
    }

    function calcPoolInGivenSingleOut(
        uint tokenBalanceOut,
        uint poolSupply,
        uint tokenAmountOut
    )
        internal pure
        returns (uint poolAmountIn)
    {
        uint newTokenBalanceOut = bsub(
            tokenBalanceOut, 
            tokenAmountOut
        );
        uint tokenOutRatio = bdiv(newTokenBalanceOut, tokenBalanceOut);
        uint poolRatio = bsub(BONE,tokenOutRatio);
        uint newPoolSupply = bmul(poolRatio, poolSupply);
        require(newPoolSupply >= 2, 'ERR_TOKEN_AMOUNT_OUT_TOO_LOW'); 
        newPoolSupply = newPoolSupply/2;
        return newPoolSupply;
    }


    

}
