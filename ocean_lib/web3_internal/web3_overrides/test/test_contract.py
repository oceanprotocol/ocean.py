#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from ocean_lib.models.test.conftest import *  # noqa
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.test.test_contract_base import MyFactory
from ocean_lib.web3_internal.web3_overrides.contract import CustomContractFunction


@pytest.mark.unit
def test_main(web3, config, nft_factory_address):
    factory = MyFactory(web3, nft_factory_address)
    fn_args = (
        "NFT",
        "NFTS",
        1,
        ZERO_ADDRESS,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        True,
        web3.eth.accounts[0],
    )
    contract_fn = getattr(factory.contract.functions, "deployERC721Contract")(*fn_args)
    custom_contract = CustomContractFunction(contract_fn)

    with pytest.raises(ValueError):
        custom_contract.transact(
            {"data": "test"},
            config.block_confirmations.value,
            config.transaction_timeout.value,
        )

    with pytest.raises(ValueError):
        custom_contract = CustomContractFunction(contract_fn)
        custom_contract._contract_function.address = None
        custom_contract.transact(
            {}, config.block_confirmations.value, config.transaction_timeout.value
        )
