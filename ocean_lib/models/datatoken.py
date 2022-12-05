#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import Optional, Tuple, Union

from brownie.network.state import Chain
from enforce_typing import enforce_types
from web3 import Web3

from ocean_lib.ocean.util import get_address_of_type
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS

to_checksum_address = ContractBase.to_checksum_address
toWei, fromWei = Web3.toWei, Web3.fromWei


class DatatokenRoles(IntEnum):
    MINTER = 0
    PAYMENT_MANAGER = 1


class Datatoken(ContractBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10**18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    #======================================================================
    # Priced data: fixed-rate exchange

    @enforce_types
    def create_fixed_rate(self, price, base_token_address: str,amount, tx_dict):
        """
        For this datataken, create a fixed-rate exchange.

        This wraps the smart contract method Datatoken.createFixedRate()
          with a simpler interface.

        :param: price - how many base tokens does 1 datatoken cost? In wei or str
        :param: base_token_address - e.g. OCEAN address
        :param: amount - make how many datatokens available, in wei or str
        :tx_dict: e.g. {"from": alice_wallet}
        :return: exchange_id
        """
        base_token = Datatoken(self.config_dict, base_token_address)
        from_address = tx_dict["from"].address
        
        fixed_price_address = get_address_of_type(self.config_dict, "FixedPrice")
        self.approve(fixed_price_address, amount, tx_dict)

        receipt = self.contract.createFixedRate(
            to_checksum_address(fixed_price_address),
            [
                to_checksum_address(base_token.address),
                to_checksum_address(from_address), # owner
                to_checksum_address(from_address), # pub_mkt_swap_fee_rec
                to_checksum_address(ZERO_ADDRESS), # allowed_swapper
            ],
            [
                base_token.decimals(),
                self.decimals(),
                price,     # fixed_rate
                int(1e15), # publish_market_swap_fee_amount
                0,         # with_mint
            ],
            tx_dict,
        )
        
        fixed_price_address == receipt.events["NewFixedRate"]["exchangeContract"]

        exchange_id = receipt.events["NewFixedRate"]["exchangeId"]

        return exchange_id        


    @enforce_types
    def buy(self, datatoken_amt, exchange_id, tx_dict):
        """
        Buy datatokens via fixed-rate exchange.

        This wraps the smart contract method FixedRateExchange.buyDT()
          with a simpler interface.

        :param: exchange_id -- 
        :param: datatoken_amt -- how many DT to buy? In wei, or str
        :tx_dict: e.g. {"from": alice_wallet}
        :return: tx_result
        """
        # auto-compute basetoken_amt
        exchange_status = self.exchange_status(exchange_id)
        price = exchange_status.fixedRate
        price_float = float(fromWei(price,"ether"))
                            
        if isinstance(datatoken_amt, str):
            assert "ether" in datatoken_amt, "only currently handles ether"
            datatoken_amt = toWei(int(datatoken_amt.split()[0]), "ether")
        datatoken_amt_float = float(fromWei(datatoken_amt, "ether"))
                                      
        max_basetoken_amt = toWei(datatoken_amt_float*price_float*1.2,"ether")

        # approve for FRE to spend basetokens
        FRE_addr = get_address_of_type(self.config_dict, "FixedPrice")
        basetoken = Datatoken(self.config_dict, exchange_status.baseToken)
        basetoken.approve(FRE_addr, max_basetoken_amt, tx_dict)

        # peform the buy
        tx = self._ocean_fixed_rate_exchange().buyDT(
            exchange_id,
            datatoken_amt,
            max_basetoken_amt,
            ZERO_ADDRESS, #consumeMarketAddress
            0, #consumeMarketSwapFeeAmount
            tx_dict,
        )
        return tx


    @enforce_types
    def exchange_status(self, exchange_id):
        """:return: FixedRateExchangeStatus object"""
        # import here to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import FixedRateExchangeStatus

        status_tup = self._ocean_fixed_rate_exchange().getExchange(exchange_id)
        return FixedRateExchangeStatus(status_tup)


    @enforce_types
    def _ocean_fixed_rate_exchange(self):
        """:return: FixedRateExchange object"""
        # import here to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import FixedRateExchange

        FRE_addr = get_address_of_type(self.config_dict, "FixedPrice")
        return FixedRateExchange(self.config_dict, FRE_addr)


    @enforce_types
    def get_fixed_rate_exchanges(self) -> list:
        """:return: list of exchange_id -- all the exchanges for this datatoken"""
        addrs_and_exchange_ids = self.getFixedRates()
        exchange_ids = [item[1] for item in addrs_and_exchange_ids]  
        return exchange_ids

    # ===========================================================================
    # consume
    @enforce_types
    def start_order(
        self,
        consumer: str,
        service_index: int,
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: Union[int, str],
        v: int,
        r: Union[str, bytes],
        s: Union[str, bytes],
        valid_until: int,
        provider_data: Union[str, bytes],
        consume_market_order_fee_address: str,
        consume_market_order_fee_token: str,
        consume_market_order_fee_amount: int,
        transaction_parameters: dict,
    ) -> str:
        return self.contract.startOrder(
            to_checksum_address(consumer),
            service_index,
            (
                to_checksum_address(provider_fee_address),
                to_checksum_address(provider_fee_token),
                int(provider_fee_amount),
                v,
                r,
                s,
                valid_until,
                provider_data,
            ),
            (
                to_checksum_address(consume_market_order_fee_address),
                to_checksum_address(consume_market_order_fee_token),
                consume_market_order_fee_amount,
            ),
            transaction_parameters,
        )

    @enforce_types
    def reuse_order(
        self,
        order_tx_id: Union[str, bytes],
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: Union[int, str],
        v: int,
        r: Union[str, bytes],
        s: Union[str, bytes],
        valid_until: int,
        provider_data: Union[str, bytes],
        transaction_parameters: dict,
    ) -> str:
        return self.contract.reuseOrder(
            order_tx_id,
            (
                to_checksum_address(provider_fee_address),
                to_checksum_address(provider_fee_token),
                int(provider_fee_amount),
                v,
                r,
                s,
                valid_until,
                provider_data,
            ),
            transaction_parameters,
        )

    @enforce_types
    def get_start_order_logs(
        self,
        consumer_address: Optional[str] = None,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
    ) -> Tuple:
        chain = Chain()
        to_block = to_block if to_block != "latest" else chain[-1].number

        return self.contract.events.get_sequence(from_block, to_block, "OrderStarted")

    #======================================================================
    # Free data: dispenser faucet
    
    @enforce_types
    def create_dispenser(
        self,
        tx_dict: dict,
        max_tokens: Optional[int] = None,
        max_balance: Optional[int] = None,
    ):
        """
        For this datataken, create a dispenser faucet for free tokens.

        This wraps the smart contract method Datatoken.createDispenser()
          with a simpler interface.

        :param: max_tokens - max # tokens to dispense, in wei
        :param: max_balance - max balance of requester
        :tx_dict: e.g. {"from": alice_wallet}
        :return: tx
        """
        # already created, so nothing to do
        if self.dispenser_status().active:
            return

        # set max_tokens, max_balance if needed
        max_tokens = max_tokens or MAX_UINT256
        max_balance = max_balance or MAX_UINT256

        # args for contract tx
        dispenser_addr = get_address_of_type(self.config_dict, "Dispenser")
        with_mint = True  # True -> can always mint more
        allowed_swapper = ZERO_ADDRESS  # 0 -> so anyone can call dispense

        # do contract tx
        tx = self.createDispenser(
            dispenser_addr,
            max_tokens,
            max_balance,
            with_mint,
            allowed_swapper,
            tx_dict,
        )
        return tx

    @enforce_types
    def dispense(self, amount: Union[int, str], tx_dict: dict):
        """
        Dispense free tokens via the dispenser faucet.

        :param: amount - number of tokens to dispense, in wei
        :tx_dict: e.g. {"from": alice_wallet}
        :return: tx
        """
        # args for contract tx
        datatoken_addr = self.address
        from_addr = tx_dict["from"].address

        # do contract tx
        tx = self._ocean_dispenser().dispense(
            datatoken_addr, amount, from_addr, tx_dict
        )
        return tx

    @enforce_types
    def dispenser_status(self):
        """:return: DispenserStatus object"""
        # import here to avoid circular import
        from ocean_lib.models.dispenser import DispenserStatus

        status_tup = self._ocean_dispenser().status(self.address)
        return DispenserStatus(status_tup)

    @enforce_types
    def _ocean_dispenser(self):
        """:return: Dispenser object"""
        # import here to avoid circular import
        from ocean_lib.models.dispenser import Dispenser

        dispenser_addr = get_address_of_type(self.config_dict, "Dispenser")
        return Dispenser(self.config_dict, dispenser_addr)


class MockERC20(Datatoken):
    CONTRACT_NAME = "MockERC20"


class MockOcean(Datatoken):
    CONTRACT_NAME = "MockOcean"
