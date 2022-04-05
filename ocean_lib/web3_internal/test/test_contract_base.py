#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#

import pytest
from enforce_typing import enforce_types
from web3.contract import ContractCaller

from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.contract_base import ContractBase
from ocean_lib.web3_internal.wallet import Wallet


class MyFactory(ContractBase):
    CONTRACT_NAME = "ERC721Factory"

    # super-simple functionality, because our main point here is to
    # test ContractBase itself, not a child class.
    @enforce_types
    def deploy_erc721_contract(self, erc721_data, from_wallet: Wallet):
        return self.send_transaction("deployERC721Contract", erc721_data, from_wallet)


@pytest.mark.unit
def test_name_is_None(web3):
    with pytest.raises(AssertionError):
        # self.name will become None, triggering the error
        ContractBase(web3, None)


@pytest.mark.unit
def test_nochild(web3):
    with pytest.raises(AssertionError):
        ContractBase(web3, None)


@pytest.mark.unit
def test_main(network, alice_wallet, alice_ocean, nft_factory_address, web3):

    # test super-simple functionality of child
    factory = MyFactory(web3, nft_factory_address)
    factory.deploy_erc721_contract(
        (
            "NFT",
            "NFTS",
            1,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            "https://oceanprotocol.com/nft/",
            True,
            alice_wallet.address,
        ),
        alice_wallet,
    )

    # test attributes
    assert factory.name == "ERC721Factory"
    assert isinstance(factory.contract.caller, ContractCaller)
    assert factory.contract is not None
    assert factory.contract.address == nft_factory_address
    assert ContractBase.to_checksum_address(nft_factory_address) == nft_factory_address

    # test methods
    assert "configured_address" in dir(factory)
    assert factory.contract_name == "ERC721Factory"
    assert factory.address == nft_factory_address
    assert factory.events
    assert str(factory) == f"{factory.contract_name} @ {factory.address}"
    assert (
        "createToken" in factory.function_names
    ), "The function createToken from the contract does not exist."
    assert "getCurrentTokenCount" in factory.function_names
    assert "getTokenTemplate" in factory.function_names
    with pytest.raises(ValueError):
        assert factory.get_event_signature("noevent")

    assert factory.subscribe_to_event("NFTCreated", 30, None) is None
    assert factory.get_event_argument_names("NFTCreated") == ()
    block = web3.eth.block_number
    block_confirmations = alice_ocean.config.block_confirmations.value
    assert (
        len(
            factory.get_event_logs(
                "NFTCreated",
                block - block_confirmations,
                block - block_confirmations,
                None,
            )
        )
        == 1
    ), "The token was not created."
    log = factory.get_event_log(
        "NFTCreated", block - block_confirmations, block - block_confirmations, None
    )
    assert len(log) == 1, "The token was not created."
    assert log[0]["event"] == "NFTCreated"
    assert log[0]["address"] == nft_factory_address

    with pytest.raises(TypeError):
        ContractBase.getLogs(None)


@pytest.mark.unit
def test_gas_price(web3, alice_wallet, nft_factory_address, monkeypatch):
    monkeypatch.setenv("GAS_PRICE", "1")
    factory = MyFactory(web3, nft_factory_address)
    assert factory.deploy_erc721_contract(
        (
            "NFT",
            "NFTS",
            1,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            "https://oceanprotocol.com/nft/",
            True,
            alice_wallet.address,
        ),
        alice_wallet,
    ), "The token could not be created by configuring the gas price env var."
