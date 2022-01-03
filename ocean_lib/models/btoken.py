#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class BTokenBase(ContractBase):
    CONTRACT_NAME = "BTokenBase"

    def symbol(self) -> str:
        """
        :return: str
        """
        return self.contract.caller.symbol()

    def decimals(self) -> int:
        """
        :return: int
        """
        return self.contract.caller.decimals()

    def balanceOf(self, address: str) -> int:
        """
        :return: int
        """
        return self.contract.caller.balanceOf(address)

    def increase_approval(self, dst: str, amt: int, from_wallet: Wallet) -> str:
        """
        :return: hex str transaction hash
        """
        return self.send_transaction("increaseApproval", (dst, amt), from_wallet)

    def decrease_approval(self, dst: str, amt: int, from_wallet: Wallet):
        """
        :return: hex str transaction hash
        """
        return self.send_transaction("decreaseApproval", (dst, amt), from_wallet)

    def approve(self, spender_address: str, amt: int, from_wallet: Wallet) -> str:
        """
        :return: hex str transaction hash
        """
        return self.send_transaction("approve", (spender_address, amt), from_wallet)

    def transfer(self, dst_address: str, amt: int, from_wallet: Wallet) -> str:
        """
        :return: hex str transaction hash
        """
        return self.send_transaction("transfer", (dst_address, amt), from_wallet)

    def transfer_from(self, src: str, dst: str, amt: int, from_wallet: Wallet) -> str:
        """
        :return: hex str transaction hash
        """
        return self.send_transaction("transferFrom", (src, dst, amt), from_wallet)

    def allowance(self, src_address: str, dst_address: str) -> int:
        """
        :return: int
        """
        return self.contract.caller.allowance(src_address, dst_address)
