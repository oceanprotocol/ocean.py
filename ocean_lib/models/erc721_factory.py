#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types
from ocean_lib.models.erc_token_factory_base import ERCTokenFactoryBase
from ocean_lib.web3_internal.wallet import Wallet


@enforce_types
class ERC721FactoryContract(ERCTokenFactoryBase):
    CONTRACT_NAME = "ERC721Factory"

    def deploy_erc721_contract(
        self,
        name: str,
        symbol: int,
        data: bytes,
        flags: bytes,
        template_index: int,
        from_wallet: Wallet,
    ):
        return self.send_transaction(
            "deployERC721Contract",
            (name, symbol, data, flags, template_index),
            from_wallet,
        )
