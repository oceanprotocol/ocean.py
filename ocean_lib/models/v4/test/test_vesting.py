#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.bpool import BPool
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData, PoolData
from ocean_lib.models.v4.side_staking import SideStaking
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import get_address_of_type


def test_main(
    web3,
    config,
    consumer_wallet,
    publisher_wallet,
    another_consumer_wallet,
    factory_router,
):
    """Tests main test flow."""

    vesting_amount = web3.toWei("0.0018", "ether")

    erc721_factory = ERC721FactoryContract(
        web3,
        get_address_of_type(config, "ERC721Factory"),
    )

    # Tests deploy erc721
    tx = erc721_factory.deploy_erc721_contract(
        "NFT",
        "NFTS",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    registered_event = erc721_factory.get_event_log(
        ERC721FactoryContract.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert registered_event[0].event == "NFTCreated"
    assert registered_event[0].args.admin == publisher_wallet.address
    erc721_contract = ERC721Token(
        web3=web3, address=registered_event[0].args.newTokenAddress
    )

    symbol = erc721_contract.symbol()
    assert symbol == "NFTS"

    owner_balance = erc721_contract.contract.caller.balanceOf(publisher_wallet.address)
    assert owner_balance == 1
    assert erc721_factory.get_nft_template(0)

    # Tests roles
    erc721_contract.add_manager(another_consumer_wallet.address, publisher_wallet)

    erc721_contract.add_to_create_erc20_list(
        consumer_wallet.address, another_consumer_wallet
    )
    erc721_contract.add_to_metadata_list(
        consumer_wallet.address, another_consumer_wallet
    )
    erc721_contract.add_to_725_store_list(
        consumer_wallet.address, another_consumer_wallet
    )

    permissions = erc721_contract.get_permissions(consumer_wallet.address)

    assert permissions[1] == True
    assert permissions[2] == True
    assert permissions[3] == True

    # Tests user 3 deploys an ERC20DT
    erc_data = ErcCreateData(
        1,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [
            consumer_wallet.address,
            another_consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        [web3.toWei(0.05, "ether"), 0],
        [b""],
    )

    trx_erc_20 = erc721_contract.create_erc20(erc_data, consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(trx_erc_20)
    assert tx_receipt.status == 1

    event = erc721_factory.get_event_log(
        ERC721Token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    dt_address = event[0].args.newTokenAddress
    erc_token = ERC20Token(web3=web3, address=dt_address)
 
    # Tests permissions
    perms = erc_token.permissions(consumer_wallet.address)
    assert perms[0] == True

    # Tests user 3 deploys pool and check market fee
    initial_ocean_liq = web3.toWei(0.02, "ether")
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, "Router"),
        web3.toWei(0.02, "ether"),
        consumer_wallet,
    )

    pool_data = PoolData(
        [
            web3.toWei(1, "ether"),
            ocean_contract.decimals(),
            initial_ocean_liq // 100 * 9,
            2500000,
            initial_ocean_liq,
        ],
        [
            web3.toWei(0.001, "ether"),
            web3.toWei(0.001, "ether"),
        ],
        [
            get_address_of_type(config, "Staking"),
            ocean_contract.address,
            consumer_wallet.address,
            consumer_wallet.address,
            get_address_of_type(config, "OPFCommunityFeeCollector"),
            get_address_of_type(config, "poolTemplate"),
        ],
    )
    tx = erc_token.deploy_pool(pool_data, consumer_wallet)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = factory_router.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert pool_event[0].event == "NewPool"
    b_pool_address = pool_event[0].args.poolAddress
    b_pool = BPool(web3, b_pool_address)
    assert b_pool.is_finalized() == True
    assert b_pool.opf_fee() == 0
    assert b_pool.get_swap_fee() == web3.toWei(0.001, "ether")
    assert b_pool.community_fee(get_address_of_type(config, "Ocean")) == 0
    assert b_pool.community_fee(erc_token.address) == 0
    assert b_pool.market_fee(get_address_of_type(config, "Ocean")) == 0
    assert b_pool.market_fee(erc_token.address) == 0

    assert erc_token.balanceOf(get_address_of_type(config, "Staking")) == web3.toWei(
        0.03, "ether"
    )

    # user 3 fails to mint new erc20 token even if the minter
    perms = erc_token.permissions(consumer_wallet.address)
    assert perms[0] == True

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc_token.mint(consumer_wallet.address, 1, consumer_wallet)
        assert (
            err.value.args[0]
            == "execution reverted: VM Exception while processing transaction: revert DataTokenTemplate: cap exceeded"
        )

    assert erc_token.balanceOf(consumer_wallet.address) == 0

    # check if the vesting amount is correct

    side_staking = SideStaking(
        web3=web3, address=get_address_of_type(config, "Staking")
    )
    assert side_staking.get_vesting_amount(erc_token.address) == vesting_amount
