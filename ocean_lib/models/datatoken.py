#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import Optional, Tuple, Union

from brownie import Wei
from brownie.network.state import Chain
from enforce_typing import enforce_types

from ocean_lib.models.fixed_rate_exchange import \
    FixedRateExchange, FreFees, FreStatus
from ocean_lib.ocean.util import get_address_of_type, to_wei, from_wei
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS

to_checksum_address = ContractBase.to_checksum_address


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
    def create_fixed_rate(
            self,
            price,
            base_token_addr: str,
            amount,
            tx_dict,
            auto_approve_owner_dt=True,
            owner_addr=None,
            market_fee_collector_addr=None,
            market_fee=0,
            with_mint=False,
            allowed_swapper=ZERO_ADDRESS):
        """
        For this datataken, create a fixed-rate exchange.

        This wraps the smart contract method Datatoken.createFixedRate()
          with a simpler interface. May also do DT.approve()

        Main params:
        - price - how many base tokens does 1 datatoken cost? In wei or str
        - base_token_addr - e.g. OCEAN address
        - amount - make how many datatokens available, in wei or str
        - tx_dict - e.g. {"from": alice_wallet}

        Optional params, with good defaults
        - auto_approve_owner_dt - if True and owner==from_addr, then DT.approve
        - owner_addr
        - market_fee_collector_addr - Default to publisher
        - market_fee - in wei or str, e.g. int(1e15) or "0.001 ether"
        - with_mint - bool
        - allowed_swapper - if ZERO_ADDRESS, anyone can swap

        Return
        - exchange_id -
        - tx_receipts - list of tx_receipt, in order they happened
        """
        FRE_addr = get_address_of_type(self.config_dict, "FixedPrice")
        from_addr = tx_dict["from"].address
        BT = Datatoken(self.config_dict, base_token_addr)      
        owner_addr = owner_addr or from_addr
        market_fee_collector_addr = market_fee_collector_addr or from_addr

        tx_receipts = []
        if auto_approve_owner_dt and owner_addr == from_addr:
            tx_receipt = self.approve(FRE_addr, amount, tx_dict)
            tx_receipts.append(tx_receipt)

        tx_receipt = self.contract.createFixedRate(
            to_checksum_address(FRE_addr),
            [
                to_checksum_address(BT.address),
                to_checksum_address(owner_addr),
                to_checksum_address(market_fee_collector_addr),
                to_checksum_address(allowed_swapper),
            ],
            [
                BT.decimals(),
                self.decimals(),
                price,
                market_fee,
                with_mint,
            ],
            tx_dict,
        )
        tx_receipts.append(tx_receipt)

        exchange_id = tx_receipt.events["NewFixedRate"]["exchangeId"]
        return (exchange_id, tx_receipts)


    @enforce_types
    def buy(self,
            datatoken_amt,
            exchange_id,
            tx_dict,
            max_basetoken_amt=None):
        """
        Buy datatokens via fixed-rate exchange.

        This wraps the smart contract method FixedRateExchange.buyDT()
          with a simpler interface. It also calls basetoken.approve().

        Main params:
        - datatoken_amt - how many DT to buy? In wei, or str
        - exchange_id -
        - tx_dict - e.g. {"from": alice_wallet}

        Optional params, with good defaults:
        - max_basetoken_amt - maximum to spend. Default is caller's balance.

        Return
        - tx_receipts - list of tx_receipt, in order they happened
        """
        FRE = self._FRE()
        fees = FRE.fees(exchange_id)
        status = FRE.status(exchange_id)
        assert status.datatoken == self.address, "exchange_id isn't for this dt"
        BT = Datatoken(self.config_dict, status.baseToken)
        buyer_addr = tx_dict["from"].address

        if max_basetoken_amt is None:
            max_basetoken_amt = FRE.BT_needed(exchange_id, datatoken_amt).val
        max_basetoken_amt = Wei(max_basetoken_amt)
        assert BT.balanceOf(buyer_addr) >= max_basetoken_amt, "not enough funds"

        tx_receipt0 = BT.approve(FRE.address, max_basetoken_amt, tx_dict)

        # # do we need this??
        # datatoken_amt = Wei(datatoken_amt)
        # assert DT.allowance(carlos.address, FRE.address) >= datatoken_amt
        
        tx_receipt1 = FRE.buyDT(
            exchange_id,
            datatoken_amt,
            max_basetoken_amt,
            fees.marketFeeCollector,
            fees.marketFee,
            tx_dict,
        )
        tx_receipts = [tx_receipt0, tx_receipt1]
        return tx_receipts


    @enforce_types
    def sell(self, datatoken_amt, exchange_id, tx_dict, min_basetoken_amt=0):
        """
        Sell datatokens to the exchange, in return for e.g. OCEAN
        from the exchange's reserved

        This wraps the smart contract method FixedRateExchange.sellDT()
          with a simpler interface. It also calls datatoken.approve()

        Main params:
        - datatoken_amt - how many DT to sell? In wei, or str
        - exchange_id -
        - tx_dict - e.g. {"from": alice_wallet}

        Optional params, with good defaults:
        - min_basetoken_amt - min basetoken to get back
        """
        FRE = self._FRE()
        fees = FRE.fees(exchange_id)
        status = FRE.status(exchange_id)
        assert status.datatoken == self.address, "exchange_id isn't for this dt"

        self.approve(FRE.address, datatoken_amt, tx_dict)

        tx_receipt = FRE.sellDT(
            exchange_id,
            datatoken_amt,
            min_basetoken_amt,
            fees.marketFeeCollector,
            fees.marketFee,
            tx_dict,
        )
        return tx_receipt

    def _FRE(self) -> FixedRateExchange:
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
