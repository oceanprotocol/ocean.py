#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.models.bconst import BConst


class BTokenBase(BConst):
    CONTRACT_NAME = "BTokenBase"

    @enforce_types
    def token_name(self) -> str:
        return self.contract.name()

    @enforce_types
    def symbol(self) -> str:
        return self.contract.symbol()

    @enforce_types
    def decimals(self) -> int:
        return self.contract.decimals()

    @enforce_types
    def balanceOf(self, address: str) -> int:
        return self.contract.balanceOf(address)

    @enforce_types
    def increase_approval(self, dst: str, amt: int, from_wallet) -> str:
        return self.send_transaction("increaseApproval", (dst, amt), from_wallet)

    @enforce_types
    def decrease_approval(self, dst: str, amt: int, from_wallet) -> str:
        return self.send_transaction("decreaseApproval", (dst, amt), from_wallet)

    @enforce_types
    def approve(self, spender_address: str, amt: int, from_wallet) -> str:
        return self.send_transaction("approve", (spender_address, amt), from_wallet)

    @enforce_types
    def transfer(self, dst_address: str, amt: int, from_wallet) -> str:
        return self.send_transaction("transfer", (dst_address, amt), from_wallet)

    @enforce_types
    def transfer_from(self, src: str, dst: str, amt: int, from_wallet) -> str:
        return self.send_transaction("transferFrom", (src, dst, amt), from_wallet)

    @enforce_types
    def allowance(self, src_address: str, dst_address: str) -> int:
        return self.contract.allowance(src_address, dst_address)

    @enforce_types
    def total_supply(self) -> int:
        return self.contract.totalSupply()
