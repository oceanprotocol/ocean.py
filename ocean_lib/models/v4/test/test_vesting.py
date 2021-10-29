#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from web3 import exceptions
from web3.main import Web3

from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.models_structures import ErcCreateData, PoolData
from ocean_lib.ocean.util import get_contracts_addresses
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import (
    get_publisher_wallet,
    get_consumer_wallet,
    get_another_consumer_wallet,
)

_NETWORK = "development"


def get_nft_factory_address(config):
    """Helper function to retrieve a known ERC721 factory address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses[ERC721FactoryContract.CONTRACT_NAME]


def get_nft_template_address(config):
    """Helper function to retrieve a known ERC721 template address."""
    addresses = get_contracts_addresses(config.address_file, _NETWORK)

    return addresses[ERC721Token.CONTRACT_NAME]


def test_properties(web3, config):
    """Tests the events' properties."""
    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))
    assert (
        erc721_factory.event_NFTCreated.abi["name"]
        == ERC721FactoryContract.EVENT_NFT_CREATED
    )
    assert (
        erc721_factory.event_TokenCreated.abi["name"]
        == ERC721FactoryContract.EVENT_TOKEN_CREATED
    )
    assert (
        erc721_factory.event_NewPool.abi["name"] == ERC721FactoryContract.EVENT_NEW_POOL
    )
    assert (
        erc721_factory.event_NewFixedRate.abi["name"]
        == ERC721FactoryContract.EVENT_NEW_FIXED_RATE
    )

def test_deploy_erc721_contract(web3:Web3,config):
    publisher = get_publisher_wallet()

    erc721_factory = ERC721FactoryContract(web3, get_nft_factory_address(config))

    tx = erc721_factory.deploy_erc721_contract("NFT","NFTS",1,ZERO_ADDRESS,"https://oceanprotocol.com/nft/",publisher)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED, tx_receipt.blockNumber,web3.eth.block_number,None
    )
    assert registered_event[0].event == "NFTCreated"
    assert registered_event[0].args.admin == publisher.address
    erc721Token = ERC721Token(web3=web3,address=registered_event[0].args.newTokenAddress)

    symbol = erc721Token.symbol()
    assert symbol == "NFTS"

    ownerBalance = erc721Token.contract.caller.balanceOf(publisher.address)
    assert ownerBalance == 1
    assert erc721_factory.get_nft_template(0)
    return erc721Token

def test_roles(web3:Web3,config):
    publisher = get_publisher_wallet()
    user3 = get_consumer_wallet()
    user2 = get_another_consumer_wallet()

    erc721Token = test_deploy_erc721_contract(web3,config)
    erc721Token.add_manager(user2.address,publisher)

    erc721Token.add_to_create_erc20_list(user3.address,user2)
    erc721Token.add_to_metadata_list(user3.address,user2)
    erc721Token.add_to_725_store_list(user3.address,user2)

    permissions = erc721Token.get_permissions(user3.address)

    assert permissions[1] == True
    assert permissions[2] == True
    assert permissions[3] == True

    return erc721Token

def test_user3_deploys_erc20dt(web3:Web3,config):
    v4Addresses = get_contracts_addresses(
        address_file=config.address_file, network=_NETWORK
    )

    publisher = get_publisher_wallet()
    user3 = get_consumer_wallet()
    user2 = get_another_consumer_wallet()
    erc721Token = test_roles(web3,config)
    nftFactory = ERC721FactoryContract(web3=web3, address=v4Addresses["ERC721Factory"])

    ercData = ErcCreateData(
        1,
        ["ERC20DT1","ERC20DT1Symbol"],
        [user3.address,user2.address,publisher.address,ZERO_ADDRESS],
        [web3.toWei(10000,"ether"),0],
        [],
    )
    trxErc20 = erc721Token.create_erc20(ercData,user3) 
    receipt = web3.eth.wait_for_transaction_receipt(trxErc20)
    assert receipt["status"] == 1
    
    event = nftFactory.get_event_log(
        ERC721Token.EVENT_TOKEN_CREATED, receipt.blockNumber,web3.eth.block_number,None)

    dt_address = event[0].args.newTokenAddress
    
    ercToken = ERC20Token(web3=web3,address=dt_address)
    perms = ercToken.permissions(user3.address)

    assert True == perms[0]

    return ercToken,erc721Token

def test_user3_deploypool_marketfee(web3,config):
    v4Addresses = get_contracts_addresses(
        address_file=config.address_file, network=_NETWORK
    )
    publisher = get_publisher_wallet()
    user3 = get_consumer_wallet()
    user2 = get_another_consumer_wallet()

    ercToken,erc721Token = test_user3_deploys_erc20dt(web3,config)

    ssDtBalance = ercToken.balanceOf(v4Addresses["Staking"])

    initialOceanLiq = web3.toWei(2000,"ether")
    initialDtLiq = initialOceanLiq

    oceanContract = ERC20Token(web3=web3,address=v4Addresses["Ocean"])
    oceanContract.approve(v4Addresses["Router"],web3.toWei(2000,"ether"),user3)
    print(oceanContract.balanceOf(user3.address))

    poolData = PoolData(
        [v4Addresses["Staking"],v4Addresses["Ocean"],user3.address,v4Addresses["OPFCommunityFeeCollector"],v4Addresses["poolTemplate"]],
        [
            web3.toWei(1,"ether"),
            18,
            web3.toWei(10000,"ether"),
            2500000,
            initialOceanLiq
        ],
        [
            web3.toWei(0.001,"ether"),
            web3.toWei(0.001,"ether")
        ]
    )
    tx = ercToken.deploy_pool(poolData,user3)
    print(tx)

    assert 0