#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.factory_router import FactoryRouter
from ocean_lib.web3_internal.currency import to_wei


def test_balancer_constants(factory_router: FactoryRouter):
    assert factory_router.get_bone() == to_wei(1)
    assert factory_router.get_min_bound_tokens() == 2
    assert factory_router.get_max_bound_tokens() == 2
    assert factory_router.get_min_fee() == to_wei("0.0001")  # 0.01%
    assert factory_router.get_max_fee() == to_wei("0.1")  # 10%
    assert factory_router.get_exit_fee() == to_wei(0)
    assert factory_router.get_min_weight() == to_wei(1)
    assert factory_router.get_max_weight() == to_wei(50)
    assert factory_router.get_max_total_weight() == to_wei(50)
    assert factory_router.get_min_balance() == to_wei("0.000_000_000_001")
    assert factory_router.get_init_pool_supply() == to_wei(100)
    assert factory_router.get_min_bpow_base() == to_wei("0.000_000_000_000_000_001")
    assert factory_router.get_max_bpow_base() == to_wei("1.999_999_999_999_999_999")
    assert factory_router.get_max_in_ratio() == to_wei("0.5")
    assert factory_router.get_max_out_ratio() == to_wei("0.500_000_000_000_000_001")
