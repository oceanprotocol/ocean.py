#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from enum import IntEnum
from typing import Any, Dict, List, Optional, Tuple, Union

from brownie.network.state import Chain
from enforce_typing import enforce_types
from web3.main import Web3

from ocean_lib.agreements.service_types import ServiceTypes
from ocean_lib.models.fixed_rate_exchange import OneExchange
from ocean_lib.ocean.util import (
    from_wei,
    get_address_of_type,
    get_from_address,
    get_ocean_token_address,
    str_with_wei,
    to_wei,
)
from ocean_lib.services.service import Service
from ocean_lib.structures.file_objects import FilesType
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase

checksum_addr = ContractBase.to_checksum_address
logger = logging.getLogger("ocean")


class TokenFeeInfo:
    def __init__(
        self,
        address: Optional[str] = None,
        token: Optional[str] = None,
        amount: Optional[int] = 0,
    ):
        self.address = (
            Web3.toChecksumAddress(address.lower()) if address else ZERO_ADDRESS
        )
        self.token = Web3.toChecksumAddress(token.lower()) if token else ZERO_ADDRESS

        self.amount = amount

    def to_tuple(self):
        return (self.address, self.token, self.amount)

    @classmethod
    def from_tuple(cls, tup):
        address, token, amount = tup
        return cls(address, token, amount)

    def __str__(self):
        s = (
            f"TokenFeeInfo: \n"
            f"  address = {self.address}\n"
            f"  token = {self.token}\n"
            f"  amount = {str_with_wei(self.amount)}\n"
        )
        return s


class DatatokenArguments:
    def __init__(
        self,
        name: Optional[str] = "Datatoken 1",
        symbol: Optional[str] = "DT1",
        template_index: Optional[int] = 1,
        minter: Optional[str] = None,
        fee_manager: Optional[str] = None,
        publish_market_order_fees: Optional = None,
        bytess: Optional[List[bytes]] = None,
        services: Optional[list] = None,
        files: Optional[List[FilesType]] = None,
        consumer_parameters: Optional[List[Dict[str, Any]]] = None,
        cap: Optional[int] = None,
    ):
        if template_index == 2 and not cap:
            raise Exception("Cap is needed for Datatoken Enterprise token deployment.")

        self.cap = cap if template_index == 2 else MAX_UINT256

        self.name = name
        self.symbol = symbol
        self.template_index = template_index
        self.minter = minter
        self.fee_manager = fee_manager
        self.bytess = bytess or [b""]
        self.services = services
        self.files = files
        self.consumer_parameters = consumer_parameters

        self.publish_market_order_fees = publish_market_order_fees or TokenFeeInfo()
        self.set_default_fees_at_deploy = not publish_market_order_fees

    def create_datatoken(self, data_nft, tx_dict, with_services=False):
        config_dict = data_nft.config_dict
        OCEAN_address = get_ocean_token_address(config_dict)
        initial_list = data_nft.getTokensList()

        wallet_address = get_from_address(tx_dict)

        if self.set_default_fees_at_deploy:
            self.publish_market_order_fees = TokenFeeInfo(
                address=wallet_address, token=OCEAN_address
            )

        data_nft.contract.createERC20(
            self.template_index,
            [self.name, self.symbol],
            [
                ContractBase.to_checksum_address(self.minter or wallet_address),
                ContractBase.to_checksum_address(self.fee_manager or wallet_address),
                self.publish_market_order_fees.address,
                self.publish_market_order_fees.token,
            ],
            [self.cap, self.publish_market_order_fees.amount],
            self.bytess,
            tx_dict,
        )

        new_elements = [
            item for item in data_nft.getTokensList() if item not in initial_list
        ]
        assert len(new_elements) == 1, "new data token has no address"

        from ocean_lib.models.datatoken_enterprise import DatatokenEnterprise

        datatoken = (
            Datatoken(config_dict, new_elements[0])
            if self.template_index == 1
            else DatatokenEnterprise(config_dict, new_elements[0])
        )

        logger.info(
            f"Successfully created datatoken with address " f"{datatoken.address}."
        )

        if with_services:
            if not self.services:
                self.services = [
                    datatoken.build_access_service(
                        service_id="0",
                        service_endpoint=config_dict.get("PROVIDER_URL"),
                        files=self.files,
                        consumer_parameters=self.consumer_parameters,
                    )
                ]
            else:
                for service in self.services:
                    service.datatoken = datatoken.address

        return datatoken


class DatatokenRoles(IntEnum):
    MINTER = 0
    PAYMENT_MANAGER = 1


class Datatoken(ContractBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10**18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    # ===========================================================================
    # consume

    @enforce_types
    def start_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        tx_dict: dict,
        consume_market_fees=None,
    ) -> str:

        if not consume_market_fees:
            consume_market_fees = TokenFeeInfo()

        return self.contract.startOrder(
            checksum_addr(consumer),
            service_index,
            (
                checksum_addr(provider_fees["providerFeeAddress"]),
                checksum_addr(provider_fees["providerFeeToken"]),
                int(provider_fees["providerFeeAmount"]),
                provider_fees["v"],
                provider_fees["r"],
                provider_fees["s"],
                provider_fees["validUntil"],
                provider_fees["providerData"],
            ),
            consume_market_fees.to_tuple(),
            tx_dict,
        )

    @enforce_types
    def reuse_order(
        self,
        order_tx_id: Union[str, bytes],
        provider_fees: dict,
        tx_dict: dict,
    ) -> str:
        return self.contract.reuseOrder(
            order_tx_id,
            (
                checksum_addr(provider_fees["providerFeeAddress"]),
                checksum_addr(provider_fees["providerFeeToken"]),
                int(provider_fees["providerFeeAmount"]),
                provider_fees["v"],
                provider_fees["r"],
                provider_fees["s"],
                provider_fees["validUntil"],
                provider_fees["providerData"],
            ),
            tx_dict,
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

    # ======================================================================
    # Priced data: fixed-rate exchange

    @enforce_types
    def create_exchange(
        self,
        rate: Union[int, str],
        base_token_addr: str,
        tx_dict: dict,
        owner_addr: Optional[str] = None,
        publish_market_fee_collector: Optional[str] = None,
        publish_market_fee: Union[int, str] = 0,
        with_mint: bool = False,
        allowed_swapper: str = ZERO_ADDRESS,
        full_info: bool = False,
    ) -> Union[OneExchange, tuple]:
        """
        For this datatoken, create a single fixed-rate exchange (OneExchange).

        This wraps the smart contract method Datatoken.createFixedRate()
          with a simpler interface

        Main params:
        - rate - how many base tokens does 1 datatoken cost? In wei or str
        - base_token_addr - e.g. OCEAN address
        - tx_dict - e.g. {"from": alice_wallet}

        Optional params, with good defaults
        - owner_addr
        - publish_market_fee_collector - fee going to publish mkt
        - publish_market_fee - in wei or str, e.g. int(1e15) or "0.001 ether"
        - with_mint - should the exchange mint datatokens as needed, or
          do they need to by supplied/allowed by participants like base token?
        - allowed_swapper - if ZERO_ADDRESS, anyone can swap
        - full_info - return just OneExchange, or (OneExchange, <other info>)

        Return
        - exchange - OneExchange
        - (maybe) tx_receipt
        """
        # import now, to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import OneExchange

        FRE_addr = get_address_of_type(self.config_dict, "FixedPrice")
        from_addr = get_from_address(tx_dict)
        BT = Datatoken(self.config_dict, base_token_addr)
        owner_addr = owner_addr or from_addr
        publish_market_fee_collector = publish_market_fee_collector or from_addr

        tx = self.contract.createFixedRate(
            checksum_addr(FRE_addr),
            [
                checksum_addr(BT.address),
                checksum_addr(owner_addr),
                checksum_addr(publish_market_fee_collector),
                checksum_addr(allowed_swapper),
            ],
            [
                BT.decimals(),
                self.decimals(),
                rate,
                publish_market_fee,
                with_mint,
            ],
            tx_dict,
        )

        exchange_id = tx.events["NewFixedRate"]["exchangeId"]
        FRE = self._FRE()
        exchange = OneExchange(FRE, exchange_id)
        if full_info:
            return (exchange, tx)
        return exchange

    @enforce_types
    def get_exchanges(self) -> list:
        """return List[OneExchange] - all the exchanges for this datatoken"""
        # import now, to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import OneExchange

        FRE = self._FRE()
        addrs_and_exchange_ids = self.getFixedRates()
        exchanges = [
            OneExchange(FRE, exchange_id) for _, exchange_id in addrs_and_exchange_ids
        ]
        return exchanges

    @enforce_types
    def _FRE(self):
        """Return FixedRateExchange - global across all exchanges"""
        # import now, to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import FixedRateExchange

        FRE_addr = get_address_of_type(self.config_dict, "FixedPrice")
        return FixedRateExchange(self.config_dict, FRE_addr)

    # ======================================================================
    # Free data: dispenser faucet

    @enforce_types
    def create_dispenser(
        self,
        tx_dict: dict,
        max_tokens: Optional[Union[int, str]] = None,
        max_balance: Optional[Union[int, str]] = None,
        with_mint: Optional[bool] = True,
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
        with_mint = with_mint  # True -> can always mint more
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
        from_addr = get_from_address(tx_dict)

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

    @enforce_types
    def build_access_service(
        self,
        service_id: str,
        service_endpoint: str,
        files: List[FilesType],
        timeout: Optional[int] = 3600,
        consumer_parameters=None,
    ) -> Service:
        return Service(
            service_id=service_id,
            service_type=ServiceTypes.ASSET_ACCESS,
            service_endpoint=service_endpoint,
            datatoken=self.address,
            files=files,
            timeout=timeout,
            consumer_parameters=consumer_parameters,
        )

    def dispense_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        tx_dict: dict,
        consume_market_fees=None,
    ) -> str:
        if not consume_market_fees:
            consume_market_fees = TokenFeeInfo()

        buyer_addr = get_from_address(tx_dict)

        bal = from_wei(self.balanceOf(buyer_addr))
        if bal < 1.0:
            dispenser_addr = get_address_of_type(self.config_dict, "Dispenser")
            from ocean_lib.models.dispenser import Dispenser  # isort: skip

            dispenser = Dispenser(self.config_dict, dispenser_addr)

            # catch key failure modes
            st = dispenser.status(self.address)
            active, allowedSwapper = st[0], st[6]
            if not active:
                raise ValueError("No active dispenser for datatoken")
            if allowedSwapper not in [ZERO_ADDRESS, buyer_addr]:
                raise ValueError(f"Not allowed. allowedSwapper={allowedSwapper}")

            # Try to dispense. If other issues, they'll pop out
            dispenser.dispense(self.address, "1 ether", buyer_addr, tx_dict)

        return self.start_order(
            consumer=ContractBase.to_checksum_address(consumer),
            service_index=service_index,
            provider_fees=provider_fees,
            consume_market_fees=consume_market_fees,
            tx_dict=tx_dict,
        )

    @enforce_types
    def buy_DT_and_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: dict,
        exchange: Any,
        tx_dict: dict,
        consume_market_fees=None,
    ) -> str:
        fre_address = get_address_of_type(self.config_dict, "FixedPrice")

        # import now, to avoid circular import
        from ocean_lib.models.fixed_rate_exchange import OneExchange

        if not consume_market_fees:
            consume_market_fees = TokenFeeInfo()

        if not isinstance(exchange, OneExchange):
            exchange = OneExchange(fre_address, exchange)

        exchange.buy_DT(
            datatoken_amt=to_wei(1),
            consume_market_fee_addr=consume_market_fees.address,
            consume_market_fee=consume_market_fees.amount,
            tx_dict=tx_dict,
        )

        return self.start_order(
            consumer=ContractBase.to_checksum_address(consumer),
            service_index=service_index,
            provider_fees=provider_fees,
            consume_market_fees=consume_market_fees,
            tx_dict=tx_dict,
        )

    def get_publish_market_order_fees(self):
        return TokenFeeInfo.from_tuple(self.contract.getPublishingMarketFee())


class MockERC20(Datatoken):
    CONTRACT_NAME = "MockERC20"


class MockOcean(Datatoken):
    CONTRACT_NAME = "MockOcean"
