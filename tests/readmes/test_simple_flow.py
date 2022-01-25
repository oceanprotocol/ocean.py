#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os

from ocean_lib.example_config import ExampleConfig
from ocean_lib.models.models_structures import CreateErc20Data
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.wallet import Wallet


def test_simple_flow():

    private_key = os.getenv("TEST_PRIVATE_KEY1")
    config = ExampleConfig.get_config()
    ocean = Ocean(config)

    wallet = Wallet(
        ocean.web3, private_key, config.block_confirmations, config.transaction_timeout
    )

    erc721_token = ocean.create_nft_token(
        name="Dataset name", symbol="dtsymbol", from_wallet=wallet
    )

    assert erc721_token.address
    assert erc721_token.token_name() == "Dataset name"
    assert erc721_token.symbol() == "dtsymbol"

    cap = ocean.to_wei(10)
    erc20_data = CreateErc20Data(
        template_index=1,  # default value
        strings=["ERC20DT1", "ERC20DT1Symbol"],  # name & symbol for ERC20 token
        addresses=[
            wallet.address,  # minter address
            wallet.address,  # fee manager for this ERC20 token
            wallet.address,  # publishing Market Address
            ZERO_ADDRESS,  # publishing Market Fee Token
        ],
        uints=[cap, 0],
        bytess=[b""],
    )
    erc20_token = erc721_token.create_datatoken(
        erc20_data=erc20_data, from_wallet=wallet
    )

    assert erc20_token.address
    assert erc20_token.token_name() == "ERC20DT1"
    assert erc20_token.symbol() == "ERC20DT1Symbol"
