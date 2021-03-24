#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from ocean_lib.models.test.conftest import dtfactory_address
from ocean_lib.ocean.util import to_base_18
from ocean_lib.web3_internal.test.test_contract_base import MyFactory
from ocean_lib.web3_internal.web3_overrides.contract import CustomContractFunction


def test_main():
    factory = MyFactory(dtfactory_address)
    # factory.createToken("foo_blob", "DT1", "DT1", to_base_18(1000), alice_wallet)
    fn_args = ("foo_blob", "DT1", "DT1", to_base_18(1000))
    contract_fn = getattr(factory.contract.functions, "createToken")(*fn_args)
    custom_contract = CustomContractFunction(contract_fn)

    # TODO: None transaction doesn't actually work.
    # assert custom_contract.transact() == None

    with pytest.raises(ValueError):
        custom_contract.transact({"data": "test"})

    with pytest.raises(ValueError):
        custom_contract = CustomContractFunction(contract_fn)
        custom_contract._contract_function.address = None
        custom_contract.transact()
