#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Permissions, ERC721Token
from ocean_lib.web3_internal.constants import BLOB, ZERO_ADDRESS
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


def test_properties(web3, config):
    """Tests the events' properties."""
    erc721_token_address = get_address_of_type(config, ERC721Token.CONTRACT_NAME)
    erc721_token = ERC721Token(web3, erc721_token_address)

    assert (
        erc721_token.event_TokenCreated.abi["name"] == ERC721Token.EVENT_TOKEN_CREATED
    )
    assert (
        erc721_token.event_MetadataCreated.abi["name"]
        == ERC721Token.EVENT_METADATA_CREATED
    )
    assert (
        erc721_token.event_MetadataUpdated.abi["name"]
        == ERC721Token.EVENT_METADATA_UPDATED
    )


def test_main_flow(web3, config, publisher_wallet, consumer_wallet):
    """Tests utils' functions."""
    erc721_factory_address = get_address_of_type(
        config, ERC721FactoryContract.CONTRACT_NAME
    )
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert erc721_token.contract.caller.name() == "NFT"
    assert erc721_token.symbol() == "NFTSYMBOL"
    assert erc721_token.balance_of(publisher_wallet.address) == 1

    # Tests if the NFT was initialized
    assert erc721_token.is_initialized() is True

    # Tests adding a manager successfully
    erc721_token.add_manager(consumer_wallet.address, publisher_wallet)
    assert erc721_token.get_permissions(consumer_wallet.address)[
        ERC721Permissions.MANAGER
    ]

    assert erc721_token.token_uri(1) == "https://oceanprotocol.com/nft/1"

    # Tests failing to re-initialize the contract
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.initialize(
            publisher_wallet.address,
            "NewName",
            "NN",
            erc721_factory_address,
            ZERO_ADDRESS,
            "https://oceanprotocol.com/nft/",
            publisher_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: token instance "
        "already initialized"
    )


def test_fails_update_metadata(web3, config, publisher_wallet, consumer_wallet):
    """Tests failure of calling update metadata function when the role of the user is not METADATA UPDATER."""
    erc721_token = deploy_erc721_erc20(web3, config, publisher_wallet)
    assert (
        erc721_token.get_permissions(consumer_wallet.address)[
            ERC721Permissions.UPDATE_METADATA
        ]
        is False
    )
    with pytest.raises(exceptions.ContractLogicError) as err:
        erc721_token.set_metadata(
            1,
            "http://myprovider:8030",
            "0x123",
            flags=web3.toBytes(hexstr=BLOB),
            data=web3.toBytes(hexstr=BLOB),
            data_hash=web3.toBytes(hexstr=BLOB),
            from_wallet=consumer_wallet,
        )
    assert (
        err.value.args[0]
        == "execution reverted: VM Exception while processing transaction: revert ERC721Template: NOT METADATA_ROLE"
    )
