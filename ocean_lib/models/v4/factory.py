#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from typing import List

from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class IFactory(ContractBase):
    @enforce_types
    def initialize(
        self,
        name: str,
        symbol: str,
        minter: str,
        cap: int,
        blob: str,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "initialize",
            (name, symbol, minter, cap, blob, from_wallet.address),
            from_wallet,
        )

    @enforce_types
    def is_initialized(self, from_wallet: Wallet) -> str:
        return self.send_transaction("isInitialized", from_wallet)

    @enforce_types
    def createToken(
        self,
        template_index: int,
        strings: List[str],
        addresses: List[str],
        uints: List[int],
        bytess: bytes,
        from_wallet: Wallet,
    ) -> str:
        return self.send_transaction(
            "createToken",
            (template_index, strings, addresses, uints, bytess),
            from_wallet,
        )

    @enforce_types
    def add_to_ERC721_registry(self, ERC721address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("addToERC721Registry", ERC721address, from_wallet)

    @enforce_types
    def erc721_list(self, ERC721address: str, from_wallet: Wallet) -> str:
        return self.send_transaction("erc721List", ERC721address, from_wallet)

    @enforce_types
    def erc20_list(self, data_token: str, from_wallet: Wallet) -> str:
        return self.send_transaction("erc20List", data_token, from_wallet)
