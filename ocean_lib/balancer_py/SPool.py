import enforce
import typing

from .BToken import BToken
from ..util import util
from ..util.util import ETHfromBase, ETHtoBase

@enforce.runtime_validation
class SPool(BToken):    
    def __init__(self, c: util.Context, pool_address: str):
        self._c: util.Context = c
        abi = self._abi()
        self.contract = c.web3.eth.contract(address=pool_address, abi=abi)
        self.f = self.contract.functions
        
    @property
    def address(self):
        return self.contract.address

    def _BToken(self, token_address: str) -> BToken:
        return BToken(self._c, token_address)

    def __str__(self):
        s = []
        s += ["SPool:"]
        s += [f"  pool_address={self.contract.address}"]
        s += [f"  controller address = {self.getController()}"]
        s += [f"  isPublicSwap = {self.isPublicSwap()}"]
        s += [f"  isFinalized = {self.isFinalized()}"]

        swap_fee = ETHfromBase(self.getSwapFee_base())
        s += ["  swapFee = %.2f%%" % (swap_fee * 100.0)]
        
        s += [f"  numTokens = {self.getNumTokens()}"]
        cur_addrs = self.getCurrentTokens()
        cur_symbols = [self._BToken(addr).symbol() for addr in cur_addrs]
        s += [f"  currentTokens (as symbols) = {', '.join(cur_symbols)}"]

        if self.isFinalized():
            final_addrs = self.getFinalTokens()
            final_symbols = [self._BToken(addr).symbol() for addr in final_addrs]
            s += [f"  finalTokens (as symbols) = {final_symbols}"]
            
        s += [f"  is bound:"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            s += [f"    {symbol}: {self.isBound(addr)}"]

        s += [f"  weights (fromBase):"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            denorm_w = ETHfromBase(self.getDenormalizedWeight_base(addr))
            norm_w = ETHfromBase(self.getNormalizedWeight_base(addr))
            s += [f"    {symbol}: denorm_w={denorm_w}, norm_w={norm_w} "]

        total_denorm_w = ETHfromBase(self.getTotalDenormalizedWeight_base())
        s += [f"    total_denorm_w={total_denorm_w}"]
        
        s += [f"  balances (fromBase):"]
        for addr, symbol in zip(cur_addrs, cur_symbols):
            balance_base = self.getBalance_base(addr)
            dec = self._BToken(addr).decimals()
            balance = util.fromBase(balance_base, dec)
            s += [f"    {symbol}: {balance}"]

        return "\n".join(s)

    def _abi(self):
        return util.abi(filename='./abi/SPool.abi')

    #============================================================
    #keeps solidity calls short
    def doTx(self, func):
        (tx_hash, tx_receipt) = util.buildAndSendTx(self._c, func)
    
    #============================================================
    #reflect SPool Solidity methods: everything at Balancer Interfaces "SPool"
    # docstrings are adapted from Balancer API 
    # https://docs.balancer.finance/smart-contracts/api

    #==== View Functions
    def isPublicSwap(self) -> bool:
        return self.f.isPublicSwap().call()

    def isFinalized(self) -> bool:
        """
        The `finalized` state lets users know that the weights, balances, and
        fees of this pool are immutable. In the `finalized` state, `SWAP`, 
        `JOIN`, and `EXIT` are public. `CONTROL` capabilities are disabled.
        (https://docs.balancer.finance/smart-contracts/api#access-control)
        """
        return self.f.isFinalized().call()
    
    def isBound(self, token_address: str) -> bool:
        """
        A bound token has a valid balance and weight. A token cannot be bound 
        without valid parameters which will enable e.g. `getSpotPrice` in terms
        of other tokens. However, disabling `isSwapPublic` will disable any 
        interaction with this token in practice (assuming there are no existing
        tokens in the pool, which can always `exitPool`).
        """
        return self.f.isBound(token_address).call()    

    def getNumTokens(self) -> int:
        """
        How many tokens are bound to this pool.
        """
        return self.f.getNumTokens().call()

    def getCurrentTokens(self) -> typing.List[str]:
        """@return -- list of [token_addr:str]"""
        return self.f.getCurrentTokens().call()

    def getFinalTokens(self) -> typing.List[str]:
        """@return -- list of [token_addr:str]"""
        return self.f.getFinalTokens().call()

    def getDenormalizedWeight_base(self, token_address: str) -> int:
        return self.f.getDenormalizedWeight(token_address).call()

    def getTotalDenormalizedWeight_base(self) -> int:
        return self.f.getTotalDenormalizedWeight().call()

    def getNormalizedWeight_base(self, token_address: str) -> int:
        """
        The normalized weight of a token. The combined normalized weights of 
        all tokens will sum up to 1. (Note: the actual sum may be 1 plus or 
        minus a few wei due to division precision loss)
        """
        return self.f.getNormalizedWeight(token_address).call()

    def getBalance_base(self, token_address: str) -> int:
        return self.f.getBalance(token_address).call()

    def getSwapFee_base(self) -> int:
        return self.f.getSwapFee().call()

    def getController(self) -> str:
        """
        Get the "controller" address, which can call `CONTROL` functions like 
        `rebind`, `setSwapFee`, or `finalize`.
        """
        return self.f.getController().call()

    #==== Controller Functions

    def setSwapFee(self, swapFee_base: int):
        """
        Caller must be controller. Pool must NOT be finalized.
        """
        self.doTx(self.f.setSwapFee(swapFee_base))
        
    def setController(self, manager_address: str):
        self.doTx(self.f.setController(manager_address))

    def setPublicSwap(self, public: bool):
        """
        Makes `isPublicSwap` return `_publicSwap`. Requires caller to be 
        controller and pool not to be finalized. Finalized pools always have 
        public swap.
        """
        self.doTx(self.f.setPublicSwap(public))
        
    def finalize(self):
        """
        This makes the pool **finalized**. This is a one-way transition. `bind`,
        `rebind`, `unbind`, `setSwapFee` and `setPublicSwap` will all throw 
        `ERR_IS_FINALIZED` after pool is finalized. This also switches 
        `isSwapPublic` to true.
        """
        self.doTx(self.f.finalize())
    
    def bind(self, token_address: str, balance_base: int, weight_base: int):
        """
        Binds the token with address `token`. Tokens will be pushed/pulled from 
        caller to adjust match new balance. Token must not already be bound. 
        `balance` must be a valid balance and denorm must be a valid denormalized
        weight. `bind` creates the token record and then calls `rebind` for 
        updating pool weights and token transfers.

        Possible errors:
        -`ERR_NOT_CONTROLLER` -- caller is not the controller
        -`ERR_IS_BOUND` -- T is already bound
        -`ERR_IS_FINALIZED` -- isFinalized() is true
        -`ERR_ERC20_FALSE` -- ERC20 token returned false
        -`ERR_MAX_TOKENS` -- Only 8 tokens are allowed per pool
        -unspecified error thrown by token
        """
        self.doTx(self.f.bind(token_address, balance_base, weight_base))

    def rebind(self, token_address: str, balance_base: int, weight_base: int):
        """
        Changes the parameters of an already-bound token. Performs the same 
        validation on the parameters.
        """
        self.doTx(self.f.rebind(token_address, balance_base, weight_base))
        
    def unbind(self, token_address: str):
        """
        Unbinds a token, clearing all of its parameters. Exit fee is charged
        and the remaining balance is sent to caller.
        """
        self.doTx(self.f.unbind(token_address))
    
    def gulp(self, token_address: str):
        """
        This syncs the internal `balance` of `token` within a pool with the 
        actual `balance` registered on the ERC20 contract. This is useful to 
        account for airdropped tokens or any tokens sent to the pool without 
        using the `join` or `joinSwap` methods. 

        As an example, pools that contain `COMP` tokens can have the `COMP`
        balance updated with the rewards sent by Compound (https://etherscan.io/tx/0xeccd42bf2b8a180a561c026717707d9024a083059af2f22c197ee511d1010e23). 
        In order for any airdrop balance to be gulped, the token must be bound 
        to the pool. So if a shared pool (which is immutable) does not have a 
        given token, any airdrops in that token will be locked in the pool 
        forever. 
        """
        self.doTx(self.f.gulp(token_address))
        
    #==== Price Functions

    def getSpotPrice_base(
            self, tokenIn_address:str, tokenOut_address: str) -> int:
        return self.f.getSpotPrice(
            tokenIn_address, tokenOut_address).call()

    def getSpotPriceSansFee_base(
            self, tokenIn_address: str, tokenOut_address: str) -> int:
        return self.f.getSpotPriceSansFee(
            tokenIn_address, tokenOut_address).call()

    #==== Trading and Liquidity Functions

    def joinPool(
            self,
            poolAmountOut_base: int,
            maxAmountsIn_base: typing.List[int]):
        """
        Join the pool, getting `poolAmountOut` pool tokens. This will pull some
        of each of the currently trading tokens in the pool, meaning you must 
        have called `approve` for each token for this pool. These values are
        limited by the array of `maxAmountsIn` in the order of the pool tokens.
        """
        self.doTx(self.f.joinPool(poolAmountOut_base, maxAmountsIn_base))

    def exitPool(
            self,
            poolAmountIn_base: int,
            minAmountsOut_base : typing.List[int]):
        """
        Exit the pool, paying `poolAmountIn` pool tokens and getting some of 
        each of the currently trading tokens in return. These values are 
        limited by the array of `minAmountsOut` in the order of the pool tokens.
        """
        self.doTx(self.f.exitPool(poolAmountIn_base, minAmountsOut_base))
        
    def swapExactAmountIn(
            self,
            tokenIn_address: str,
            tokenAmountIn_base: int,
            tokenOut_address: str,
            minAmountOut_base: int,
            maxPrice_base: int):
        """
        Trades an exact `tokenAmountIn` of `tokenIn` taken from the caller by 
        the pool, in exchange for at least `minAmountOut` of `tokenOut` given 
        to the caller from the pool, with a maximum marginal price of 
        `maxPrice`.
        
        Returns `(tokenAmountOut`, `spotPriceAfter)`, where `tokenAmountOut` 
        is the amount of token that came out of the pool, and `spotPriceAfter`
        is the new marginal spot price, ie, the result of `getSpotPrice` after
        the call. (These values are what are limited by the arguments; you are 
        guaranteed `tokenAmountOut >= minAmountOut` and 
        `spotPriceAfter <= maxPrice)`.
        """
        self.doTx(self.f.swapExactAmountIn(
            tokenIn_address, tokenAmountIn_base,
            tokenOut_address, minAmountOut_base, maxPrice_base))
        
    def swapExactAmountOut(
            self,
            tokenIn_address: str,
            maxAmountIn_base: int,
            tokenOut_address: str,
            tokenAmountOut_base: int,
            maxPrice_base: int):
        self.doTx(self.f.swapExactAmountOut(
            tokenIn_address, maxAmountIn_base, tokenOut_address,
            tokenAmountOut_base, maxPrice_base))

    def joinswapExternAmountIn(
            self,
            tokenIn_address: str,
            tokenAmountIn_base: int,
            minPoolAmountOut_base: int):
        """
        Pay `tokenAmountIn` of token `tokenIn` to join the pool, getting
        `poolAmountOut` of the pool shares.
        """
        self.doTx(self.f.joinswapExternAmountIn(
            tokenIn_address, tokenAmountIn_base, minPoolAmountOut_base))
                  
    def joinswapPoolAmountOut(
            self,
            tokenIn_address: str,
            poolAmountOut_base: int,
            maxAmountIn_base: int):
        """
        Specify `poolAmountOut` pool shares that you want to get, and a token
        `tokenIn` to pay with. This costs `maxAmountIn` tokens (these went 
        into the pool).
        """
        self.doTx(self.f.joinswapPoolAmountOut(
            tokenIn_address, poolAmountOut_base, maxAmountIn_base))

    def exitswapPoolAmountIn(
            self,
            tokenOut_address: str,
            poolAmountIn_base: int,
            minAmountOut_base: int):
        """
        Pay `poolAmountIn` pool shares into the pool, getting `tokenAmountOut` 
        of the given token `tokenOut` out of the pool.
        """
        self.doTx(self.f.exitswapPoolAmountIn(
            tokenOut_address, poolAmountIn_base, minAmountOut_base))
        
    def exitswapExternAmountOut(
            self,
            tokenOut_address: str,
            tokenAmountOut_base: int,
            maxPoolAmountIn_base: int):
        """
        Specify `tokenAmountOut` of token `tokenOut` that you want to get out
        of the pool. This costs `poolAmountIn` pool shares (these went into 
        the pool).
        """
        self.doTx(self.f.exitswapExternAmountOut(
            tokenOut_address, tokenAmountOut_base, maxPoolAmountIn_base))
        
    #==== Balancer Pool as ERC20 
    def totalSupply_base(self) -> int:
        return self.f.totalSupply().call()
    
    def balanceOf_base(self, whom_address: str) -> int:
        return self.f.balanceOf(whom_address).call()

    def allowance_base(self, src_address: str, dst_address: str) -> int:
        return self.f.allowance(src_address, dst_address).call()
    
    def approve(self, dst_address: str, amt_base: int):
        self.doTx(self.f.approve(dst_address, amt_base))

    def transfer(self, dst_address: str, amt_base: int):
        self.doTx(self.f.transfer(dst_address, amt_base))
        
    def transferFrom(self, src_address: str, dst_address: str, amt_base: int):
        self.doTx(self.f.transferFrom(dst_address, src_address, amt_base))

    #===== Calculators
    def calcSpotPrice_base(
            self,
            tokenBalanceIn_base: int,
            tokenWeightIn_base : int,
            tokenBalanceOut_base: int,
            tokenWeightOut_base : int,
            swapFee_base : int) -> int:
        """Returns spotPrice_base"""
        return self.f.calcSpotPrice(
            tokenBalanceIn_base, tokenWeightIn_base, tokenBalanceOut_base,
            tokenWeightOut_base, swapFee_base).call()

    def calcOutGivenIn_base(
            self,
            tokenBalanceIn_base: int,
            tokenWeightIn_base : int,
            tokenBalanceOut : int,
            tokenWeightOut_base : int,
            tokenAmountIn_base : int,
            swapFee_base : int) -> int:
        """Returns tokenAmountOut_base"""
        return self.f.calcOutGivenIn(
            tokenBalanceIn_base, tokenWeightIn_base, tokenBalanceOut, 
            tokenWeightOut_base, tokenAmountIn_base, swapFee_base).call()
                       
    def calcInGivenOut_base(
            self,
            tokenBalanceIn_base: int,
            tokenWeightIn_base : int,
            tokenBalanceOut_base : int,
            tokenWeightOut_base : int,
            tokenAmountOut_base: int,
            swapFee_base: int) -> int:
        """Returns tokenAmountIn_base"""
        return self.f.calcInGivenOut(
            tokenBalanceIn_base, tokenWeightIn_base, tokenBalanceOut_base,
            tokenWeightOut_base, tokenAmountOut_base, swapFee_base).call()
    
    def calcPoolOutGivenSingleIn_base(
            self,
            tokenBalanceIn_base: int,
            tokenWeightIn_base: int,
            poolSupply_base: int,
            totalWeight_base: int,
            tokenAmountIn_base: int,
            swapFee_base: int) -> int:
        """Returns poolAmountOut_base"""
        return self.f.calcPoolOutGivenSingleIn(
            tokenBalanceIn_base, tokenWeightIn_base, poolSupply_base,
            totalWeight_base, tokenAmountIn_base, swapFee_base).call()
    
    def calcSingleInGivenPoolOut_base(
            self,
            tokenBalanceIn_base: int,
            tokenWeightIn_base: int,
            poolSupply_base: int,
            totalWeight_base: int,
            poolAmountOut_base: int,
            swapFee_base: int) -> int:
        """Returns tokenAmountIn_base"""
        return self.f.calcSingleInGivenPoolOut(
            tokenBalanceIn_base, tokenWeightIn_base, poolSupply_base,
            totalWeight_base, poolAmountOut_base, swapFee_base).call()
    
    def calcSingleOutGivenPoolIn_base(
            self,
            tokenBalanceOut_base: int,
            tokenWeightOut_base: int,
            poolSupply_base: int,
            totalWeight_base: int,
            poolAmountIn_base: int,
            swapFee_base: int) -> int:
        """Returns tokenAmountOut_base"""
        return self.f.calcSingleOutGivenPoolIn(
            tokenBalanceOut_base, tokenWeightOut_base, poolSupply_base,
            totalWeight_base, poolAmountIn_base, swapFee_base).call()
            
    def calcPoolInGivenSingleOut(
            self,
            tokenBalanceOut_base: int,
            tokenWeightOut_base: int,
            poolSupply_base: int,
            totalWeight_base: int,
            tokenAmountOut_base: int,
            swapFee_base: int) -> int:
        """Returns poolAmountIn_base"""
        return self.f.calcPoolInGivenSingleOut(
            tokenBalanceOut_base, tokenWeightOut_base, poolSupply_base,
            totalWeight_base, tokenAmountOut_base, swapFee_base).call()
