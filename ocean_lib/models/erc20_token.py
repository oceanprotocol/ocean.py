#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types
from ocean_lib.ocean.util import from_base_18
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC20Token(ContractBase):
    CONTRACT_NAME = "ERC20Template"

    BASE = 10 ** 18
    BASE_COMMUNITY_FEE_PERCENTAGE = BASE / 1000
    BASE_MARKET_FEE_PERCENTAGE = BASE / 1000

    def initialize(
        self,
        name: str,
        symbol: str,
        erc_address: str,
        cap: int,
        fee_collector_address: str,
        minter_address: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "initialize",
            (name, symbol, erc_address, cap, fee_collector_address, minter_address),
            from_wallet,
        )

    def mint(self, account_address: str, value: int, from_wallet: Wallet) -> str:
        return self.send_transaction("mint", (account_address, value), from_wallet)

    def start_order(
        self,
        consumer: str,
        amount: int,
        service_id: int,
        mrkt_fee_collector: str,
        fee_token: str,
        fee_amount: int,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "startOrder",
            (consumer, amount, service_id, mrkt_fee_collector, fee_token, fee_amount),
            from_wallet,
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

    def addMinter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addMinter", (minter_address), from_wallet)

    def removeMinter(self, minter_address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("removeMinter", (minter_address), from_wallet)

    def set_data(self, data: bytes) -> None:
        return self.contract.caller.setData(data)

    def clean_permissions(self) -> None:
        return self.contract.caller.cleanPermissions()

    def clean_from_721(self) -> None:
        return self.contract.caller.cleanFrom721()

    def set_fee_collector(self, fee_collector_address: str) -> None:
        return self.contract.caller.setFeeCollector(fee_collector_address)

    def name(self) -> str:
        return self.contract.caller.name()

    def symbol(self) -> str:
        return self.contract.caller.symbol()

    def decimals(self) -> int:
        return self.contract.caller.decimals()

    def cap(self) -> int:
        return self.contract.caller.cap()

    def is_initialized(self) -> bool:
        return self.contract.caller.isInitialized()

    def calculateFee(self, amount: int, fee_percentage: int) -> int:
        return self.contract.caller.calculateFee(amount, fee_percentage)

    def permit(
        self,
        owner_address: str,
        spender_address: str,
        value: int,
        deadline: int,
        v: int,
        r: bytes,
        s: bytes,
    ) -> str:
        return self.contract.caller.permit(
            owner_address, spender_address, value, deadline, v, r, s
        )

    def get_address_length(self, array: List[str]) -> int:
        return self.contract.caller.getAddressLength(array)

    def get_uint_length(self, array: List[int]) -> int:
        return self.contract.caller.getUintLength(array)

    def get_bytes_length(self, array: List[bytes]) -> int:
        return self.contract.caller.getBytesLength(array)

    def get_fee_collector(self) -> str:
        return self.contract.caller.getFeeCollector()

    def balanceOf(self, account: str) -> int:
        return self.contract.caller.balanceOf(account)

    def transfer(self, to: str, value_base: int, from_wallet: Wallet) -> str:
        return self.send_transaction("transfer", (to, value_base), from_wallet)

    def token_balance(self, account: str):
        return from_base_18(self.balanceOf(account))


class MockOcean(ERC20Token):
    CONTRACT_NAME = "MockOcean"
