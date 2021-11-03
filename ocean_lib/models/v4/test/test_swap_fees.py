#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.v4.dispenser import DispenserV4
from ocean_lib.models.v4.erc20_token import ERC20Token
from ocean_lib.models.v4.bpool import BPool
from ocean_lib.models.v4.erc721_factory import ERC721FactoryContract
from ocean_lib.models.v4.erc721_token import ERC721Token
from ocean_lib.models.v4.models_structures import ErcCreateData
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from tests.resources.helper_functions import get_address_of_type


def test_deploy_erc721_and_manage(
    web3, config, factory_deployer_wallet, consumer_wallet, another_consumer_wallet,publisher_wallet
):
    """
    Owner deploys a new ERC721 contract
    """
    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )
    tx = erc721_factory.deploy_erc721_contract(
        "NFT",
        "SYMBOL",
        1,
        ZERO_ADDRESS,
        "https://oceanprotocol.com/nft/",
        factory_deployer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)

    event = erc721_factory.get_event_log(
        erc721_factory.EVENT_NFT_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert event is not None

    token_address = event[0].args.newTokenAddress
    erc721_token = ERC721Token(web3, token_address)

    assert erc721_token.balance_of(factory_deployer_wallet.address) == 1

    erc721_token.add_manager(consumer_wallet.address, factory_deployer_wallet)
    erc721_token.add_to_725_store_list(
        another_consumer_wallet.address, factory_deployer_wallet
    )
    erc721_token.add_to_create_erc20_list(
        another_consumer_wallet.address, factory_deployer_wallet
    )
    erc721_token.add_to_metadata_list(
        another_consumer_wallet.address, factory_deployer_wallet
    )

    permissions = erc721_token.get_permissions(another_consumer_wallet.address)

    assert permissions[1] == True
    assert permissions[2] == True
    assert permissions[3] == True

    # * user3 deploys a new erc20DT, assigning himself as minter

    cap = web3.toWei(100000, "ether")
    tx = erc721_token.create_erc20(
        ErcCreateData(
            1,
            ["ERC20DT1", "ERC20DT1Symbol"],
            [
                another_consumer_wallet.address,
                factory_deployer_wallet.address,
                another_consumer_wallet.address,
                "0x0000000000000000000000000000000000000000",
            ],
            [cap, 0],
            [],
        ),
        another_consumer_wallet,
    )
    tx_receipt = web3.eth.waitForTransactionReceipt(tx)
    event = erc721_factory.get_event_log(
        erc721_token.EVENT_TOKEN_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    erc20_address = event[0].args.newTokenAddress
    erc20_token = ERC20Token(web3, erc20_address)

    assert erc20_token.permissions(another_consumer_wallet.address)[0] == True
    
    
    # * NOW user3 has 2 options, minting on his own and create custom pool, or using the staking contract and deploy a pool.
    # * Pool with ocean token and market fee 0.1%

    swap_fee = web3.toWei(0.001, "ether")
    swap_ocean_fee = web3.toWei(0.001, "ether")
    swap_market_fee = web3.toWei(0.001, "ether")

    # * user3 calls deployPool(), we then check ocean and market fee"

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
    tx = erc20_token.deploy_pool(pool_data, consumer_wallet)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = factory_router.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    assert pool_event[0].event == "NewPool"
    bpool_address = pool_event[0].args.poolAddress
    bpool = BPool(web3, bpool_address)
    assert bpool.is_finalized() == True
    assert bpool.opf_fee() == 0
    assert bpool.get_swap_fee() == web3.toWei(0.001, "ether")
    assert bpool.community_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.market_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(get_address_of_type(config, "Staking")) == web3.toWei(
        0.03, "ether"
    )

    assert bpool.calc_pool_in_single_out(erc20_address,web3.toWei(10,"ether")) == bpool.calc_pool_in_single_out(get_address_of_type(config,"Ocean"),web3.toWei(10,"ether"))
    assert bpool.calc_pool_out_single_in(erc20_address,web3.toWei(10,"ether")) == bpool.calc_pool_out_single_in(get_address_of_type(config,"Ocean"),web3.toWei(10,"ether"))
    assert bpool.calc_single_in_pool_out(erc20_address,web3.toWei(10,"ether")) == bpool.calc_single_in_pool_out(get_address_of_type(config,"Ocean"),web3.toWei(10,"ether"))
    assert bpool.calc_single_out_pool_in(erc20_address,web3.toWei(10,"ether")) == bpool.calc_single_out_pool_in(get_address_of_type(config,"Ocean"),web3.toWei(10,"ether"))
    
    # * user4 buys some DT - exactAmountIn

    assert ocean_contract.balanceOf(bpool.address) == web3.toWei(0.02, "ether")
    ocean_contract.approve(bpool_address, web3.toWei(0.02, "ether"), publisher_wallet)

    assert erc20_token.balanceOf(publisher_wallet.address) == 0
    user4_dt_balance = erc20_token.balanceOf(publisher_wallet.address)
    user4_ocean_balance = ocean_contract.balanceOf(publisher_wallet.address)
    ocean_market_fee_bal = bpool.market_fee(ocean_contract.address)

    tx = bpool.swap_exact_amount_in(
        ocean_contract.address,
        web3.toWei(10, "ether"),
        erc20_address,
        web3.toWei(1, "ether"),
        web3.toWei(100, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    
    assert (erc20_token.balanceOf(publisher_wallet.address) > 0) == True

    swap_fee_event = bpool.get_event_log(
        "SWAP_FEES",
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )

    swap_event_args = swap_fee_event[0].args
    # Check swap balances
    assert ocean_contract.balanceOf(publisher_wallet.address) + swap_event_args.tokenAmountIn == user4_ocean_balance
    assert erc20_token.balanceOf(publisher_wallet.address)  == user4_dt_balance + swap_event_args.tokenAmountOut


    # * user4 buys some DT - exactAmountOut
    user4_dt_balance =  erc20_token.balanceOf(publisher_wallet.address);
    user4_ocean_balance =  ocean_contract.balanceOf(publisher_wallet.address);

    dt_market_fee_bal =  bpool.marketFees(erc20_token.address);
    ocean_market_fee_bal =  bpool.marketFees(ocean_contract.address);

    tx = bpool.swap_exact_amount_out(
        ocean_contract.address,
        web3.toWei(100, "ether"),
        erc20_address,
        web3.toWei(10, "ether"),
        web3.toWei(10, "ether"),
        publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    