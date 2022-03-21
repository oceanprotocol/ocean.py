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
from ocean_lib.models.side_staking import SideStaking
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.web3_internal.constants import ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
from tests.resources.helper_functions import get_address_of_type, deploy_erc721_erc20


@pytest.mark.unit
def test_properties(config, web3):
    """Tests the events' properties."""
    side_staking_address = get_address_of_type(config, "Staking")
    side_staking = SideStaking(web3, side_staking_address)

    assert side_staking.event_Vesting.abi["name"] == SideStaking.EVENT_VESTING
    assert (
        side_staking.event_VestingCreated.abi["name"]
        == SideStaking.EVENT_VESTING_CREATED
    )


@pytest.mark.unit
def test_main(
    web3,
    config,
    consumer_wallet,
    publisher_wallet,
    another_consumer_wallet,
    factory_router,
):
    """Tests main test flow."""

    vesting_amount = to_wei(18)

    erc721_factory = ERC721FactoryContract(
        web3, get_address_of_type(config, "ERC721Factory")
    )

    # Tests deploy erc721
    tx = erc721_factory.deploy_erc721_contract(
        name="NFT",
        symbol="NFTS",
        template_index=1,
        additional_metadata_updater=ZERO_ADDRESS,
        additional_erc20_deployer=ZERO_ADDRESS,
        token_uri="https://oceanprotocol.com/nft/",
        from_wallet=publisher_wallet,
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
    trx_erc_20 = erc721_nft.create_erc20(
        template_index=1,
        datatoken_name="ERC20DT1",
        datatoken_symbol="ERC20DT1Symbol",
        datatoken_minter=consumer_wallet.address,
        datatoken_fee_manager=another_consumer_wallet.address,
        datatoken_publishing_market_address=publisher_wallet.address,
        fee_token_address=ZERO_ADDRESS,
        datatoken_cap=to_wei(1000),
        publishing_market_fee_amount=0,
        bytess=[b""],
        from_wallet=consumer_wallet,
    )

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
    mint_fake_OCEAN(config)
    initial_ocean_liq = to_wei(200)
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, "Router"), initial_ocean_liq, consumer_wallet
    )

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        basetoken_decimals=ocean_contract.decimals(),
        vesting_amount=initial_ocean_liq // 100 * 9,
        vested_blocks=2500000,
        initial_liq=initial_ocean_liq,
        lp_swap_fee=to_wei("0.003"),
        market_swap_fee=to_wei("0.001"),
        ss_contract=get_address_of_type(config, "Staking"),
        basetoken_address=ocean_contract.address,
        basetoken_sender=consumer_wallet.address,
        publisher_address=consumer_wallet.address,
        market_fee_collector=get_address_of_type(config, "OPFCommunityFeeCollector"),
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=consumer_wallet,
    )
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
    # TODO: add assert for publish market fee after contracts update merge
    assert bpool.get_swap_fee() == to_wei("0.003")
    assert bpool.community_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0

    assert erc20_token.balanceOf(get_address_of_type(config, "Staking")) == to_wei(800)

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

    # check if vesting is correct
    dt_balance_before = erc20_token.balanceOf(consumer_wallet.address)
    available_vesting_before = side_staking.get_available_vesting(erc20_token.address)
    assert available_vesting_before == 0

    # advance 100 blocks to see if available vesting increased
    for _ in range(100):
        # send 1 wei
        send_ether(consumer_wallet, ZERO_ADDRESS, 1)

    available_vesting_after = side_staking.get_available_vesting(erc20_token.address)
    assert (
        available_vesting_after > available_vesting_before
    ), "Available vesting was not increased!"
    tx_hash = side_staking.get_vesting(erc20_token.address, consumer_wallet)
    tx_result = web3.eth.wait_for_transaction_receipt(tx_hash)
    vesting_event = side_staking.get_event_log(
        SideStaking.EVENT_VESTING,
        tx_result.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert vesting_event[0].args.datatokenAddress == erc20_token.address
    assert vesting_event[0].args.publisherAddress == consumer_wallet.address
    assert vesting_event[0].args.caller == consumer_wallet.address

    # 101 blocks passed, vesting started block = tx_receipt.blockNumber (deploy pool tx)
    assert vesting_event[0].args.amountVested == int(
        (101 * vesting_amount)
        / (
            side_staking.get_vesting_end_block(erc20_token.address)
            - tx_receipt.blockNumber
        )
    )
    assert dt_balance_before < erc20_token.balanceOf(consumer_wallet.address)


@pytest.mark.slow
def test_vesting_progress(
    web3,
    config,
    publisher_wallet,
    factory_router,
):
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(1000)
    )
    mint_fake_OCEAN(config)
    initial_ocean_liq = to_wei(200)
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(
        get_address_of_type(config, "Router"), initial_ocean_liq, publisher_wallet
    )
    vested_blocks = factory_router.get_min_vesting_period()
    vesting_amount = initial_ocean_liq // 100 * 9

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        basetoken_decimals=ocean_contract.decimals(),
        vesting_amount=vesting_amount,
        vested_blocks=vested_blocks,
        initial_liq=initial_ocean_liq,
        lp_swap_fee=to_wei("0.003"),
        market_swap_fee=to_wei("0.001"),
        ss_contract=get_address_of_type(config, "Staking"),
        basetoken_address=ocean_contract.address,
        basetoken_sender=publisher_wallet.address,
        publisher_address=publisher_wallet.address,
        market_fee_collector=get_address_of_type(config, "OPFCommunityFeeCollector"),
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=publisher_wallet,
    )
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

    side_staking = SideStaking(
        web3=web3, address=get_address_of_type(config, "Staking")
    )
    vesting_created_event = side_staking.get_event_log(
        SideStaking.EVENT_VESTING_CREATED,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert vesting_created_event, "Cannot find event VestingCreated."
    assert vesting_created_event[0].args.datatokenAddress == erc20_token.address
    assert vesting_created_event[0].args.publisherAddress == publisher_wallet.address
    assert (
        vesting_created_event[0].args.vestingEndBlock
        == vested_blocks + tx_receipt.blockNumber
    )
    assert vesting_created_event[0].args.totalVestingAmount == vesting_amount

    # check if vesting is correct
    dt_balance_before = erc20_token.balanceOf(publisher_wallet.address)
    available_vesting_before = side_staking.get_available_vesting(erc20_token.address)
    assert available_vesting_before == 0

    # advance 100 blocks to see if available vesting increased
    for _ in range(vested_blocks):
        # send 1 wei
        send_ether(publisher_wallet, ZERO_ADDRESS, 1)

    available_vesting_after = side_staking.get_available_vesting(erc20_token.address)
    assert (
        available_vesting_after > available_vesting_before
    ), "Available vesting was not increased!"
    tx_hash = side_staking.get_vesting(erc20_token.address, publisher_wallet)
    tx_result = web3.eth.wait_for_transaction_receipt(tx_hash)
    vesting_event = side_staking.get_event_log(
        SideStaking.EVENT_VESTING,
        tx_result.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert vesting_event[0].args.datatokenAddress == erc20_token.address
    assert vesting_event[0].args.publisherAddress == publisher_wallet.address
    assert vesting_event[0].args.caller == publisher_wallet.address

    # vested_blocks / 2 passed
    assert (
        vesting_event[0].args.amountVested
        == side_staking.get_vesting_amount(erc20_token.address) // 2
    )
    assert dt_balance_before < erc20_token.balanceOf(publisher_wallet.address)
