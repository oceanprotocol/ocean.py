#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from abc import ABC

from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase


class ERC721TokenFactoryBase(ABC, ContractBase):
    @enforce_types
    def get_current_token_count(self) -> int:
        return self.contract.getCurrentTokenCount()

    @enforce_types
    def get_token_template(self, index: int) -> int:
        return self.contract.getTokenTemplate(index)

    @enforce_types
    def add_token_template(self, template_address: str) -> int:
        return self.contract.addTokenTemplate(template_address)

    @enforce_types
    def disable_token_template(self, index: int) -> int:
        return self.contract.disableTokenTemplate(index)

    @enforce_types
    def reactivate_token_template(self, index: int) -> int:
        return self.contract.reactivateTokenTemplate(index)

    @enforce_types
    def get_current_template_count(self) -> int:
        return self.contract.getCurrentTemplateCount()

    @enforce_types
    def is_contract(self, account_address: str) -> int:
        return self.contract.isContract(account_address)
