#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class IMetadata(ContractBase):
    @enforce_types
    def create(
        self, data_token: str, flags: bytes, data: bytes, from_wallet: Wallet
    ) -> str:
        return self.send_transaction("create", (data_token, flags, data), from_wallet)

    @enforce_types
    def update(
        self, data_token: str, flags: bytes, data: bytes, from_wallet: Wallet
    ) -> str:
        return self.send_transaction("update", (data_token, flags, data), from_wallet)
