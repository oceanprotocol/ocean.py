#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enum import IntEnum
from typing import List, Optional, Tuple, Union

from enforce_typing import enforce_types
from eth_account.messages import encode_defunct
from eth_typing.encoding import HexStr
from web3.main import Web3

from ocean_lib.models.models_structures import (
    DispenserData,
    FixedData,
    PoolData,
    ProviderFees,
)
from ocean_lib.utils.utilities import prepare_message_for_ecrecover_in_solidity
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class RolesERC20(IntEnum):
    MINTER = 0
    FEE_MANAGER = 1


@enforce_types
class ERC20Token(ContractBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10**18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    EVENT_ORDER_STARTED = "OrderStarted"
    EVENT_MINTER_PROPOSED = "MinterProposed"
    EVENT_MINTER_APPROVED = "MinterApproved"
    EVENT_NEW_POOL = "NewPool"
    EVENT_NEW_FIXED_RATE = "NewFixedRate"

    @property
    def event_OrderStarted(self):
        return self.events.OrderStarted()

    @property
    def event_MinterProposed(self):
        return self.events.MinterProposed()

    @property
    def event_MinterApproved(self):
        return self.events.MinterApproved()

    @property
    def event_NewPool(self):
        return self.events.NewPool()

    @property
    def event_NewFixedRate(self):
        return self.events.NewFixedRate()

    def initialize(
        self,
        strings: List[str],
        addresses: List[str],
        factory_addresses: List[str],
        uints: List[int],
        bytess: List[bytes],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "initialize",
            (strings, addresses, factory_addresses, uints, bytess),
            from_wallet,
        )

    def deploy_pool(
        self, pool_data: Union[dict, tuple, PoolData], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("deployPool", pool_data, from_wallet)

    def create_fixed_rate(
        self, fixed_data: Union[dict, tuple, FixedData], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("createFixedRate", fixed_data, from_wallet)

    def create_dispenser(
        self, dispenser_data: Union[dict, tuple, DispenserData], from_wallet: Wallet
    ) -> str:
        return self.send_transaction("createDispenser", dispenser_data, from_wallet)

    def mint(self, account_address: str, value: int, from_wallet: Wallet) -> str:
        return self.send_transaction("mint", (account_address, value), from_wallet)

    @staticmethod
    def sign_provider_fees(
        provider_data: bytes,
        provider_fee_address: str,
        provider_fee_token: str,
        provider_fee_amount: int,
        from_wallet: Wallet,
    ) -> Tuple[HexStr, int, str, str]:
        message = encode_defunct(
            text=f"{provider_data}{provider_fee_address}{provider_fee_token}{provider_fee_amount}"
        )
        signed_message = Web3.eth.account.sign_message(message, from_wallet.private_key)
        return prepare_message_for_ecrecover_in_solidity(signed_message)

    def start_order(
        self,
        consumer: str,
        service_index: int,
        provider_fees: Union[dict, tuple, ProviderFees],
        from_wallet: Wallet,
    ) -> str:
        # TODO: will be fixed in web3.py
        if isinstance(provider_fees, ProviderFees):
            provider_fees = tuple(provider_fees)

        return self.send_transaction(
            "startOrder", (consumer, service_index, provider_fees), from_wallet
        )

    def start_multiple_order(
        self,
        consumers: List[str],
        amounts: List[int],
        service_ids: List[int],
        mrkt_fee_collectors: List[str],
        fee_tokens: List[str],
        fee_amounts: List[int],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "startMultipleOrder",
            (
                consumers,
                amounts,
                service_ids,
                mrkt_fee_collectors,
                fee_tokens,
                fee_amounts,
            ),
            from_wallet,
        )

    def finish_order(
        self,
        order_tx_id: str,
        consumer: str,
        amount: int,
        service_id: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "finishOrder", (order_tx_id, consumer, amount, service_id), from_wallet
        )

    def finish_multiple_order(
        self,
        order_tx_ids: List[str],
        consumers: List[str],
        amounts: List[int],
        service_ids: List[int],
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "finishMultipleOrder",
            (order_tx_ids, consumers, amounts, service_ids),
            from_wallet,
        )

    def transfer(self, to: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("transfer", (to, amount), from_wallet)

    def allowance(self, owner_address: str, spender_address: str) -> int:
        return self.contract.caller.allowance(owner_address, spender_address)

    def approve(self, spender: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("approve", (spender, amount), from_wallet)

    def transferFrom(
        self, from_address: str, to_address: str, amount: int, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "transferFrom", (from_address, to_address, amount), from_wallet
        )

    def burn(self, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("burn", (amount,), from_wallet)

    def burn_from(self, from_address: str, amount: int, from_wallet: Wallet) -> str:
        return self.send_transaction("burnFrom", (from_address, amount), from_wallet)

    def is_minter(self, account: str) -> bool:
        return self.contract.caller.isMinter(account)

    def add_minter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addMinter", (minter_address,), from_wallet)

    def remove_minter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("removeMinter", (minter_address,), from_wallet)

    def add_payment_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addPaymentManager", (fee_manager,), from_wallet)

    def remove_payment_manager(self, fee_manager: str, from_wallet: Wallet) -> str:
        return self.send_transaction(
            "removePaymentManager", (fee_manager,), from_wallet
        )

    def set_data(self, data: bytes, from_wallet: Wallet) -> str:
        return self.send_transaction("setData", (data,), from_wallet)

    def clean_permissions(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanPermissions", (), from_wallet)

    def clean_from_721(self, from_wallet: Wallet) -> str:
        return self.send_transaction("cleanFrom721", (), from_wallet)

    def set_payment_collector(
        self, fee_collector_address: str, from_wallet: Wallet
    ) -> str:
        return self.send_transaction(
            "setPaymentCollector", (fee_collector_address,), from_wallet
        )

    def get_publishing_market_fee(self) -> tuple:
        return self.contract.caller.getPublishingMarketFee()

    def set_publishing_market_fee(
        self,
        publish_market_fee_address: str,
        publish_market_fee_token: str,
        publish_market_fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "setPublishingMarketFee",
            (
                publish_market_fee_address,
                publish_market_fee_token,
                publish_market_fee_amount,
            ),
            from_wallet,
        )

    def get_id(self) -> int:
        return self.contract.caller.getId()

    def token_name(self) -> str:
        return self.contract.caller.name()

    def symbol(self) -> str:
        return self.contract.caller.symbol()

    def get_erc721_address(self) -> str:
        return self.contract.caller.getERC721Address()

    def decimals(self) -> int:
        return self.contract.caller.decimals()

    def cap(self) -> int:
        return self.contract.caller.cap()

    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    def permit(
        self,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "permit",
            (owner_address, spender_address, value, deadline, v, r, s),
            from_wallet,
        )

    def get_address_length(self, array: List[str]) -> int:
        return self.contract.caller.getAddressLength(array)

    def get_uint_length(self, array: List[int]) -> int:
        return self.contract.caller.getUintLength(array)

    def get_bytes_length(self, array: List[bytes]) -> int:
        return self.contract.caller.getBytesLength(array)

    def get_payment_collector(self) -> str:
        return self.contract.caller.getPaymentCollector()

    def balanceOf(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    def withdraw(self, from_wallet: Wallet):
        return self.send_transaction("withdrawETH", (), from_wallet)

    def get_permissions(self, user: str) -> list:
        return self.contract.caller.getPermissions(user)

    def permissions(self, user: str) -> list:
        return self.contract.caller.permissions(user)

    def get_total_supply(self) -> int:
        return self.contract.caller.totalSupply()

    def get_start_order_logs(
        self,
        consumer_address: Optional[str] = None,
        from_block: Optional[int] = 0,
        to_block: Optional[int] = "latest",
        from_all_tokens: bool = False,
    ) -> Tuple:
        topic0 = self.get_event_signature(self.EVENT_ORDER_STARTED)
        topics = [topic0]
        if consumer_address:
            topic1 = f"0x000000000000000000000000{consumer_address[2:].lower()}"
            topics = [topic0, None, topic1]

        argument_filters = {"topics": topics}

        logs = self.getLogs(
            self.events.OrderStarted(),
            argument_filters=argument_filters,
            fromBlock=from_block,
            toBlock=to_block,
            from_all_addresses=from_all_tokens,
        )
        return logs


class MockERC20(ERC20Token):
    CONTRACT_NAME = "MockERC20"


class MockOcean(ERC20Token):
    CONTRACT_NAME = "MockOcean"
