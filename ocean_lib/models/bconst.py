#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.web3_internal.contract_base import ContractBase


class BConst(ContractBase):
    CONTRACT_NAME = "BConst"

    @enforce_types
    def get_bone(self) -> int:
        return self.contract.caller.BONE()

    @enforce_types
    def get_min_bound_tokens(self) -> int:
        return self.contract.caller.MIN_BOUND_TOKENS()

    @enforce_types
    def get_max_bound_tokens(self) -> int:
        return self.contract.caller.MAX_BOUND_TOKENS()

    @enforce_types
    def get_min_fee(self) -> int:
        return self.contract.caller.MIN_FEE()

    @enforce_types
    def get_max_fee(self) -> int:
        return self.contract.caller.MAX_FEE()

    @enforce_types
    def get_exit_fee(self) -> int:
        return self.contract.caller.EXIT_FEE()

    @enforce_types
    def get_min_weight(self) -> int:
        return self.contract.caller.MIN_WEIGHT()

    @enforce_types
    def get_max_weight(self) -> int:
        return self.contract.caller.MAX_WEIGHT()

    @enforce_types
    def get_max_total_weight(self) -> int:
        return self.contract.caller.MAX_TOTAL_WEIGHT()

    @enforce_types
    def get_min_balance(self) -> int:
        return self.contract.caller.MIN_BALANCE()

    @enforce_types
    def get_init_pool_supply(self) -> int:
        return self.contract.caller.INIT_POOL_SUPPLY()

    @enforce_types
    def get_min_bpow_base(self) -> int:
        return self.contract.caller.MIN_BPOW_BASE()

    @enforce_types
    def get_max_bpow_base(self) -> int:
        return self.contract.caller.MAX_BPOW_BASE()

    @enforce_types
    def get_bpow_precision(self) -> int:
        return self.contract.caller.BPOW_PRECISION()

    @enforce_types
    def get_max_out_ratio(self) -> int:
        return self.contract.caller.MAX_OUT_RATIO()

    @enforce_types
    def get_max_in_ratio(self) -> int:
        return self.contract.caller.MAX_IN_RATIO()
