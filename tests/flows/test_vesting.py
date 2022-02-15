#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT
from ocean_lib.models.models_structures import CreateErc20Data, PoolData
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
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

    vesting_amount = to_wei("0.0018")

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )

    # Tests deploy erc721
    tx = erc721_factory.deploy_erc721_contract(
        (
            "NFT",
            "NFTS",
            1,
            ZERO_ADDRESS,
            ZERO_ADDRESS,
            "https://oceanprotocol.com/nft/",
        ),
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
    erc721_nft = ERC721NFT(web3=web3, address=registered_event[0].args.newTokenAddress)

    symbol = erc721_nft.symbol()
    assert symbol == "NFTS"

    owner_balance = erc721_nft.contract.caller.balanceOf(publisher_wallet.address)
    assert owner_balance == 1

    # Tests roles
    erc721_nft.add_manager(another_consumer_wallet.address, publisher_wallet)

    erc721_nft.add_to_create_erc20_list(
        consumer_wallet.address, another_consumer_wallet
    )
    erc721_nft.add_to_metadata_list(consumer_wallet.address, another_consumer_wallet)
    erc721_nft.add_to_725_store_list(consumer_wallet.address, another_consumer_wallet)

    permissions = erc721_nft.get_permissions(consumer_wallet.address)

    assert permissions[1] is True
    assert permissions[2] is True
    assert permissions[3] is True

    # Tests consumer deploys an ERC20DT
    erc_data = CreateErc20Data(
        1,
        ["ERC20DT1", "ERC20DT1Symbol"],
        [
            consumer_wallet.address,
            another_consumer_wallet.address,
            publisher_wallet.address,
            ZERO_ADDRESS,
        ],
        [to_wei("0.05"), 0],
        [b""],
    )

    trx_erc_20 = erc721_nft.create_erc20(erc_data, consumer_wallet)

    tx_receipt = web3.eth.wait_for_transaction_receipt(trx_erc_20)
    assert tx_receipt.status == 1

    event = erc721_factory.get_event_log(
        ERC721NFT.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    dt_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3=web3, address=dt_address)

    # Tests permissions
    perms = erc20_token.get_permissions(consumer_wallet.address)
    assert perms[0] is True

    # Tests consumer deploys pool and check market fee
    initial_ocean_liq = to_wei("0.02")
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, "Router"), to_wei("0.02"), consumer_wallet
    )

    pool_data = PoolData(
        [
            to_wei(1),
            ocean_contract.decimals(),
            initial_ocean_liq // 100 * 9,
            2500000,
            initial_ocean_liq,
        ],
        [to_wei("0.001"), to_wei("0.001")],
        [
            get_address_of_type(config, "Staking"),
            ocean_contract.address,
            consumer_wallet.address,
            consumer_wallet.address,
            get_address_of_type(config, "OPFCommunityFeeCollector"),
            get_address_of_type(config, "poolTemplate"),
        ],
    )
    tx = erc20_token.deploy_pool(pool_data, consumer_wallet)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = erc20_token.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert pool_event[0].event == "NewPool", "Cannot find NewPool event"
    assert pool_event[0].args.ssContract == get_address_of_type(config, "Staking")
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)
    assert bpool.is_finalized() is True
    assert bpool.opc_fee() == 0
    assert bpool.get_swap_fee() == to_wei("0.001")
    assert bpool.community_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(get_address_of_type(config, "Staking")) == to_wei(
        "0.03"
    )

    # consumer fails to mint new erc20 token even if the minter
    perms = erc20_token.get_permissions(consumer_wallet.address)
    assert perms[0] is True

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.mint(consumer_wallet.address, 1, consumer_wallet)
        assert (
            err.value.args[0]
            == "execution reverted: VM Exception while processing transaction: revert DataTokenTemplate: cap exceeded"
        )

    assert erc20_token.balanceOf(consumer_wallet.address) == 0

    # check if the vesting amount is correct
    side_staking = SideStaking(
        web3=web3, address=get_address_of_type(config, "Staking")
    )
    assert side_staking.get_vesting_amount(erc20_token.address) == vesting_amount
