#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest

from web3 import exceptions
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.bpool import BPool
from ocean_lib.models.v4.side_staking import SideStaking
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


def test_deploy_erc721_contract(web3,config,consumer_wallet,publisher_wallet,another_consumer_wallet):
    """main test flow"""

    vesting_amount = web3.toWei('0.0018',"ether")

    v4_addresses = get_contracts_addresses(
        address_file=config.address_file, network=_NETWORK
    )
    nftFactory = ERC721FactoryContract(web3=web3, address=v4_addresses["ERC721Factory"])
    publisher = publisher_wallet
    user3 = consumer_wallet
    user2 = another_consumer_wallet

    erc721_factory = ERC721FactoryContract(web3, get_contracts_addresses(config.address_file, _NETWORK)[ERC721FactoryContract.CONTRACT_NAME])
    

    """test deploy erc721"""
    tx = erc721_factory.deploy_erc721_contract("NFT","NFTS",1,ZERO_ADDRESS,"https://oceanprotocol.com/nft/",publisher)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED, tx_receipt.blockNumber,web3.eth.block_number,None
    )
    assert registered_event[0].event == "NFTCreated"
    assert registered_event[0].args.admin == publisher.address
    erc721_contract = ERC721Token(web3=web3,address=registered_event[0].args.newTokenAddress)

    symbol = erc721_contract.symbol()
    assert symbol == "NFTS"

    ownerBalance = erc721_contract.contract.caller.balanceOf(publisher.address)
    assert ownerBalance == 1
    assert erc721_factory.get_nft_template(0)
    

    """test roles"""
    erc721_contract.add_manager(user2.address,publisher)

    erc721_contract.add_to_create_erc20_list(user3.address,user2)
    erc721_contract.add_to_metadata_list(user3.address,user2)
    erc721_contract.add_to_725_store_list(user3.address,user2)

    permissions = erc721_contract.get_permissions(user3.address)

    assert permissions[1] == True
    assert permissions[2] == True
    assert permissions[3] == True

    """test user 3 deploys an ERC20DT"""
    ercData = ErcCreateData(
        1,
        ["ERC20DT1","ERC20DT1Symbol"],
        [user3.address,user2.address,publisher.address,ZERO_ADDRESS],
        [web3.toWei(0.05,"ether"),0],
        [b""],
    )

    trxErc20 = erc721_contract.create_erc20(ercData,user3) 

    receipt = web3.eth.wait_for_transaction_receipt(trxErc20)
    assert receipt["status"] == 1
    
    event = nftFactory.get_event_log(
        ERC721Token.EVENT_TOKEN_CREATED, receipt.blockNumber,web3.eth.block_number,None)

    dt_address = event[0].args.newTokenAddress
    
    ercToken = ERC20Token(web3=web3,address=dt_address)
    perms = ercToken.permissions(user3.address)

    assert perms[0] == True

    """test permissions"""

    perms = ercToken.permissions(user3.address)

    assert True == perms[0]

    """test user 3 deploys pool and check market fee"""
    initialOceanLiq = web3.toWei(0.02,"ether")
    oceanContract = ERC20Token(web3=web3,address=v4_addresses["Ocean"])
    oceanContract.approve(v4_addresses["Router"], web3.toWei(1000,"ether"),user3)
    
    poolData = PoolData(
        [
            web3.toWei(1,"ether"),
            oceanContract.decimals(),
            initialOceanLiq // 100 * 9, 
            2500000,
            initialOceanLiq
        ],
        [
            web3.toWei(0.001,"ether"),
            web3.toWei(0.001,"ether"),
        ],
        [v4_addresses["Staking"],
        oceanContract.address,
        user3.address,
        user3.address,
        v4_addresses["OPFCommunityFeeCollector"],
        v4_addresses["poolTemplate"]]
    )
    print("BOM")
    tx = ercToken.deploy_pool(poolData,user3)
    print(tx)

    # user 3 fails to mint new erc20 token even if the minter 

    perms = ercToken.permissions(user3.address)
    assert perms[0] == True

    with pytest.raises(exceptions.ContractLogicError) as err:
        ercToken.mint(user3.address,100,user3) # TODO add assert

    assert ercToken.balanceOf(user3.address) == 0

    # check if the vesting amount is correct

    side_staking = SideStaking(web3=web3,address=v4_addresses["Staking"])
    assert side_staking.get_vesting_amount(ercToken.address) == vesting_amount

  








