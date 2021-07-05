#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.models.erc_token_factory_base import ERCTokenFactoryBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC20FactoryContract(ERCTokenFactoryBase):
    CONTRACT_NAME = "ERC20Factory"

    def create_token(
        self,
        name: str,
        symbol: int,
        cap: int,
        template_index: int,
        minter: str,
        from_wallet: Wallet,
    ):
        return self.send_transaction(
            "createToken", (name, symbol, cap, template_index, minter), from_wallet
        )

    def add_to_erc721_registry(self, erc721_address: str) -> None:
        return self.contract.caller.addToERC721Registry(erc721_address)

    def set_erc721_factory(self, erc721_address: str) -> None:
        return self.contract.caller.setERC721Factory(erc721_address)
