#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types_shim
class BToken(ContractBase):
    CONTRACT_NAME = "BToken"

    # ============================================================
    # reflect BToken Solidity methods
    def symbol(self) -> str:
        return self.contract_concise.symbol()

    def decimals(self) -> int:
        return self.contract_concise.decimals()

    def balanceOf(self, address: str) -> int:
        return self.contract_concise.balanceOf(address)

    def approve(self, spender_address: str, amt_base: int, from_wallet: Wallet):
        return self.send_transaction(
            "approve", (spender_address, amt_base), from_wallet
        )

    def transfer(self, dst_address: str, amt_base: int, from_wallet: Wallet):
        return self.send_transaction("transfer", (dst_address, amt_base), from_wallet)

    def allowance(self, src_address: str, dst_address: str) -> int:
        return self.contract_concise.allowance(src_address, dst_address)
