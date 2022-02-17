#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from abc import ABC

from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase


@enforce_types
class ERCTokenFactoryBase(ABC, ContractBase):
    def get_current_token_count(self) -> int:
        return self.contract.caller.getCurrentTokenCount()

    def get_token_template(self, index: int) -> int:
        return self.contract.caller.getTokenTemplate(index)

    def add_token_template(self, template_address: str) -> int:
        return self.contract.caller.addTokenTemplate(template_address)

    def disable_token_template(self, index: int) -> int:
        return self.contract.caller.disableTokenTemplate(index)

    def reactivate_token_template(self, index: int) -> int:
        return self.contract.caller.reactivateTokenTemplate(index)

    def get_current_template_count(self) -> int:
        return self.contract.caller.getCurrentTemplateCount()

    def is_contract(self, account_address: str) -> int:
        return self.contract.caller.isContract(account_address)
