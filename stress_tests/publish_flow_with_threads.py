#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
import threading

from ocean_lib.data_provider.data_service_provider import DataServiceProvider
from ocean_lib.example_config import ExampleConfig
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.structures.abi_tuples import CreateErc20Data
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.wallet import Wallet
from tests.resources.ddo_helpers import create_basics, build_credentials_dict
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


def _get_publishing_requirements(ocean: Ocean, wallet: Wallet):
    erc721_nft, erc20_token = deploy_erc721_erc20(ocean.web3, config, wallet, wallet)
    data_provider = DataServiceProvider
    _, metadata, encrypted_files = create_basics(config, ocean.web3, data_provider)
    return erc721_nft, erc20_token, metadata, encrypted_files


def thread_function1(ocean, wallet):
    for _ in range(1000):
        (
            erc721_nft,
            erc20_token,
            metadata,
            encrypted_files,
        ) = _get_publishing_requirements(ocean, wallet)

        erc20_data = CreateErc20Data(
            template_index=1,
            strings=["Datatoken 1", "DT1"],
            addresses=[
                wallet.address,
                wallet.address,
                ZERO_ADDRESS,
                get_address_of_type(config, "Ocean"),
            ],
            uints=[ocean.to_wei("0.5"), 0],
            bytess=[b""],
        )
        # Send 1000 requests to Aquarius for creating a plain asset with ERC20 data
        ddo = ocean.assets.create(
            metadata=metadata,
            publisher_wallet=wallet,
            encrypted_files=encrypted_files,
            erc721_address=erc721_nft.address,
            erc20_tokens_data=[erc20_data],
        )
        assert ddo, "The asset is not created."
        assert ddo.nft["name"] == "NFT"
        assert ddo.nft["symbol"] == "NFTSYMBOL"
        assert ddo.nft["address"] == erc721_nft.address
        assert ddo.nft["owner"] == wallet.address
        assert ddo.datatokens[0]["name"] == "Datatoken 1"
        assert ddo.datatokens[0]["symbol"] == "DT1"
        assert ddo.credentials == build_credentials_dict()


def thread_function2(ocean, wallet):
    for _ in range(1000):
        (
            erc721_nft,
            erc20_token,
            metadata,
            encrypted_files,
        ) = _get_publishing_requirements(ocean, wallet)
        asset = ocean.assets.create(
            metadata=metadata,
            publisher_wallet=wallet,
            encrypted_files=encrypted_files,
            erc721_address=erc721_nft.address,
            deployed_erc20_tokens=[erc20_token],
            encrypt_flag=True,
        )

        assert asset, "The asset is not created."
        assert asset.nft["name"] == "NFT"
        assert asset.nft["symbol"] == "NFTSYMBOL"
        assert asset.nft["address"] == erc721_nft.address
        assert asset.nft["owner"] == wallet.address
        assert asset.datatokens[0]["name"] == "ERC20DT1"
        assert asset.datatokens[0]["symbol"] == "ERC20DT1Symbol"
        assert asset.datatokens[0]["address"] == erc20_token.address


def thread_function3(ocean, wallet):
    for _ in range(1000):
        (
            erc721_nft,
            erc20_token,
            metadata,
            encrypted_files,
        ) = _get_publishing_requirements(ocean, wallet)
        ddo = ocean.assets.create(
            metadata=metadata,
            publisher_wallet=wallet,
            encrypted_files=encrypted_files,
            erc721_address=erc721_nft.address,
            deployed_erc20_tokens=[erc20_token],
            encrypt_flag=True,
            compress_flag=True,
        )
        assert ddo, "The asset is not created."
        assert ddo.nft["name"] == "NFT"
        assert ddo.nft["symbol"] == "NFTSYMBOL"
        assert ddo.nft["address"] == erc721_nft.address
        assert ddo.nft["owner"] == wallet.address
        assert ddo.datatokens[0]["name"] == "ERC20DT1"
        assert ddo.datatokens[0]["symbol"] == "ERC20DT1Symbol"
        assert ddo.datatokens[0]["address"] == erc20_token.address


config = ExampleConfig.get_config()
ocean = Ocean(config)

# Create Alice's wallet
alice_private_key = os.getenv("TEST_PRIVATE_KEY1")
alice_wallet = Wallet(
    ocean.web3,
    alice_private_key,
    config.block_confirmations,
    config.transaction_timeout,
)
assert alice_wallet.address

bob_private_key = os.getenv("TEST_PRIVATE_KEY2")
bob_wallet = Wallet(
    ocean.web3,
    bob_private_key,
    config.block_confirmations,
    config.transaction_timeout,
)
assert bob_wallet.address

tristan_private_key = os.getenv("TEST_PRIVATE_KEY3")
tristan_wallet = Wallet(
    ocean.web3,
    tristan_private_key,
    config.block_confirmations,
    config.transaction_timeout,
)
assert tristan_wallet.address
# Mint OCEAN
mint_fake_OCEAN(config)
assert alice_wallet.web3.eth.get_balance(alice_wallet.address) > 0, "need ETH"
assert bob_wallet.web3.eth.get_balance(bob_wallet.address) > 0, "need ETH"
assert tristan_wallet.web3.eth.get_balance(tristan_wallet.address) > 0, "need ETH"
threads = list()

t1 = threading.Thread(
    target=thread_function1,
    args=(
        ocean,
        alice_wallet,
    ),
)
threads.append(t1)
t2 = threading.Thread(
    target=thread_function2,
    args=(
        ocean,
        bob_wallet,
    ),
)
threads.append(t2)
t3 = threading.Thread(
    target=thread_function3,
    args=(
        ocean,
        tristan_wallet,
    ),
)
threads.append(t3)
t1.start()
t2.start()
t3.start()

for index, thread in enumerate(threads):
    print("Main    : before joining thread %d.", index)
    thread.join()
    print("Main    : thread %d done", index)
