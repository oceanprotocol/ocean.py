#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase


class FactoryRouter(ContractBase):
    CONTRACT_NAME = "FactoryRouter"
    EVENT_NEW_POOL = "NewPool"

    # TODO: remove alongside others with same name
    @enforce_types
    def get_opc_fee(self, base_token: str) -> int:
        return self.contract.getOPCFee(base_token)
