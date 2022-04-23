#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.bpool import BPool
from ocean_lib.models.erc20_token import ERC20Token, RolesERC20
from ocean_lib.models.erc721_factory import ERC721FactoryContract
from ocean_lib.models.erc721_nft import ERC721NFT, ERC721Permissions
from ocean_lib.ocean.mint_fake_ocean import mint_fake_OCEAN
from ocean_lib.web3_internal.constants import MAX_UINT256, ZERO_ADDRESS
from ocean_lib.web3_internal.currency import to_wei
from ocean_lib.web3_internal.transactions import send_ether
from tests.resources.helper_functions import deploy_erc721_erc20, get_address_of_type


@pytest.mark.unit
def test_permission_to_deploy_erc20(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    publisher_addr,
    consumer_addr,
    another_consumer_addr,
    erc721_factory,
    erc721_nft,
):
    """Tests permissions for ERC721 and check who has ERC20 deployer role."""
    symbol = erc721_nft.symbol()
    assert symbol == "NFTSYMBOL"

    owner_balance = erc721_nft.contract.caller.balanceOf(publisher_addr)
    assert owner_balance == 1

    # Tests roles
    erc721_nft.add_manager(another_consumer_addr, publisher_wallet)
    permissions = erc721_nft.get_permissions(another_consumer_addr)
    assert permissions[ERC721Permissions.MANAGER]
    assert not permissions[ERC721Permissions.DEPLOY_ERC20]

    erc721_nft.add_to_create_erc20_list(consumer_addr, another_consumer_wallet)
    erc721_nft.add_to_metadata_list(consumer_addr, another_consumer_wallet)
    erc721_nft.add_to_725_store_list(consumer_addr, another_consumer_wallet)

    permissions = erc721_nft.get_permissions(consumer_addr)

    assert not permissions[ERC721Permissions.MANAGER]
    assert permissions[ERC721Permissions.DEPLOY_ERC20]
    assert permissions[ERC721Permissions.UPDATE_METADATA]
    assert permissions[ERC721Permissions.STORE]


@pytest.mark.unit
def test_erc20_permissions(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    publisher_addr,
    consumer_addr,
    another_consumer_addr,
    another_consumer_wallet,
    erc721_factory,
    erc721_nft,
):
    """Tests permissions for an ERC20 token."""
    erc721_nft.add_to_create_erc20_list(consumer_addr, publisher_wallet)
    assert erc721_nft.is_erc20_deployer(consumer_addr)

    trx_erc_20 = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=consumer_addr,
        fee_manager=another_consumer_addr,
        publish_market_order_fee_address=publisher_addr,
        publish_market_order_fee_token=ZERO_ADDRESS,
        cap=to_wei(1000),
        publish_market_order_fee_amount=0,
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
    perms = erc20_token.get_permissions(consumer_addr)
    assert perms[RolesERC20.MINTER]
    assert not perms[RolesERC20.PAYMENT_MANAGER]

    erc20_token.add_payment_manager(consumer_addr, consumer_wallet)
    perms = erc20_token.get_permissions(consumer_addr)
    assert perms[RolesERC20.PAYMENT_MANAGER]


@pytest.mark.unit
def test_minting_failed_after_deploying_pool(
    web3, config, publisher_wallet, consumer_wallet, consumer_addr, factory_router
):
    """Tests failure to mint new erc20 token even if consumer has the minter role after deploying a pool."""
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3,
        config,
        erc721_publisher=publisher_wallet,
        erc20_minter=consumer_wallet,
        cap=to_wei(1000),
    )
    erc721_nft.add_to_create_erc20_list(consumer_addr, publisher_wallet)

    # Tests consumer deploys pool and check market fee
    mint_fake_OCEAN(config)

    _ = _deploy_ocean_pool(
        erc20_token=erc20_token,
        factory_router=factory_router,
        config=config,
        web3=web3,
        from_wallet=consumer_wallet,
    )

    # consumer fails to mint new erc20 token even if the minter
    perms = erc20_token.get_permissions(consumer_addr)
    assert perms[RolesERC20.MINTER]

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.mint(consumer_addr, 1, consumer_wallet)
        assert (
            err.value.args[0]
            == "execution reverted: VM Exception while processing transaction: revert DataTokenTemplate: cap exceeded"
        )


@pytest.mark.unit
def test_vesting_main_flow(web3, config, consumer_wallet, factory_router, side_staking):
    """Tests consumer deploys pool, checks fees and checks if vesting is correct after 100 blocks."""

    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, consumer_wallet, consumer_wallet, cap=to_wei(1000)
    )

    # Consumer deploys pool & checks fees
    mint_fake_OCEAN(config)
    vesting_amount = to_wei(18)
    initial_ocean_liq = to_wei(200)
    pmt_collector = erc20_token.get_payment_collector()

    block_before_deploying_pool = web3.eth.block_number
    _ = _deploy_ocean_pool(
        erc20_token=erc20_token,
        factory_router=factory_router,
        config=config,
        web3=web3,
        from_wallet=consumer_wallet,
    )
    block_deployed_pool = block_before_deploying_pool + 2
    assert (
        erc20_token.balanceOf(get_address_of_type(config, "Staking"))
        == MAX_UINT256 - initial_ocean_liq
    )

    # check if the vesting amount is correct
    assert side_staking.get_vesting_amount(erc20_token.address) == vesting_amount

    # check if vesting is correct
    dt_balance_before = erc20_token.balanceOf(erc20_token.get_payment_collector())
    available_vesting_before = side_staking.get_available_vesting(erc20_token.address)

    # advance 5 blocks to see if available vesting increased
    _advance_blocks(num_blocks=5, from_wallet=consumer_wallet)

    available_vesting_after = side_staking.get_available_vesting(erc20_token.address)
    assert (
        available_vesting_after > available_vesting_before
    ), "Available vesting was not increased!"
    tx_hash = side_staking.get_vesting(erc20_token.address, consumer_wallet)
    vested_amount = side_staking.get_amount_vested_from_event(
        tx_hash=tx_hash, erc20_token=erc20_token, from_wallet=consumer_wallet
    )

    # 5 blocks passed, vesting started block = block_deployed_pool (deploy pool tx)
    target_vesting_amount = (5 * vesting_amount) // (
        side_staking.get_vesting_end_block(erc20_token.address) - block_deployed_pool
    )
    assert vested_amount == target_vesting_amount
    assert vested_amount == side_staking.get_vesting_amount_so_far(erc20_token.address)
    assert dt_balance_before < erc20_token.balanceOf(pmt_collector)
    assert erc20_token.balanceOf(pmt_collector) == vested_amount


@pytest.mark.unit
def test_vesting_progress(
    web3,
    config,
    publisher_wallet,
    factory_router,
    side_staking,
):
    """Tests vesting progress after some percentages of the vested passed blocks."""
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(1000)
    )
    mint_fake_OCEAN(config)
    initial_ocean_liq = to_wei(200)
    vested_blocks = factory_router.get_min_vesting_period()
    percentages = [0.00000005, 0.000003, 0.00001]
    checkpoint_blocks = list(map(lambda p: int((vested_blocks * p) / 100), percentages))

    vesting_amount = initial_ocean_liq // 100 * 9

    block_before_deploying_pool = web3.eth.block_number
    _ = _deploy_ocean_pool(
        erc20_token=erc20_token,
        factory_router=factory_router,
        config=config,
        web3=web3,
        from_wallet=publisher_wallet,
    )

    # check if vesting is correct
    # it needs 2 blocks further, one for deploying pool & one for web3 call wait for tx receipt
    side_staking.check_vesting_created_event(
        block_number=block_before_deploying_pool + 2,
        erc20_token=erc20_token,
        vested_blocks=vested_blocks,
        vesting_amount=vesting_amount,
    )
    dt_balance_before = erc20_token.balanceOf(erc20_token.get_payment_collector())
    assert side_staking.get_available_vesting(erc20_token.address) == 0

    # advance checkpoint_block blocks to see if available vesting increased
    counter = 0
    for block in range(checkpoint_blocks[-1]):
        # send dummy transactions to increase block count (not part of the actual functionality)
        send_ether(publisher_wallet, ZERO_ADDRESS, 1)
        if block not in checkpoint_blocks:
            continue
        amount_vested_so_far = side_staking.get_vesting_amount_so_far(
            erc20_token.address
        )
        tx_hash = side_staking.get_vesting(erc20_token.address, publisher_wallet)

        # counter is used to count the number of times when get_vesting is called
        # (it mints another block that change the formula)
        counter += 1
        vested_amount = side_staking.get_amount_vested_from_event(
            tx_hash=tx_hash, erc20_token=erc20_token, from_wallet=publisher_wallet
        )
        target_vesting_amount = (
            int(((block + 1 + counter) * vesting_amount) / vested_blocks)
            - amount_vested_so_far
        )
        assert vested_amount == target_vesting_amount
        # claim tokens after vested blocks
        pmt_collector = erc20_token.get_payment_collector()
        assert dt_balance_before < erc20_token.balanceOf(pmt_collector)
        assert (
            erc20_token.balanceOf(pmt_collector) == vested_amount + amount_vested_so_far
        )


def test_vesting_publisher_exit_scam(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    publisher_addr,
    consumer_addr,
    another_consumer_addr,
    factory_router,
    side_staking,
):
    """Tests publisher exit scam flow when the owner of the pool claimed the datatokens from vesting,
    waits for others to add liquidity in his pool and then dumps the pool."""
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(2000)
    )

    mint_fake_OCEAN(config)
    # initial_ocean_liq = to_wei(200)
    pmt_collector = erc20_token.get_payment_collector()

    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))

    bpool = _deploy_ocean_pool(
        erc20_token=erc20_token,
        factory_router=factory_router,
        config=config,
        web3=web3,
        from_wallet=publisher_wallet,
    )

    dt_balance_before = erc20_token.balanceOf(pmt_collector)

    # advance 10 blocks to see if available vesting increased
    _advance_blocks(num_blocks=10, from_wallet=consumer_wallet)
    side_staking.get_vesting(erc20_token.address, publisher_wallet)

    # publisher receives the vested DTs after 100 mined blocks
    assert publisher_addr == pmt_collector
    assert dt_balance_before < erc20_token.balanceOf(pmt_collector)
    assert erc20_token.balanceOf(
        pmt_collector
    ) == side_staking.get_vesting_amount_so_far(erc20_token.address)

    dt_pool_balance = bpool.get_balance(erc20_token.address)
    pool_shares_before = bpool.balanceOf(publisher_addr) / bpool.total_supply()
    dt_percentage_before = pool_shares_before * bpool.get_balance(erc20_token.address)

    # another users buy DTs from the publisher pool to boost the price
    ocean_contract.approve(bpool.address, to_wei(1000000), another_consumer_wallet)
    bpool.join_swap_extern_amount_in(
        token_amount_in=ocean_contract.balanceOf(another_consumer_addr) // 100,
        min_pool_amount_out=bpool.get_balance(ocean_contract.address) // 1000,
        from_wallet=another_consumer_wallet,
    )

    ocean_contract.approve(bpool.address, to_wei(1000000), consumer_wallet)
    bpool.join_swap_extern_amount_in(
        token_amount_in=ocean_contract.balanceOf(consumer_addr) // 100,
        min_pool_amount_out=bpool.get_balance(ocean_contract.address) // 1000,
        from_wallet=consumer_wallet,
    )

    # check for increasing DT amount for publisher
    assert dt_pool_balance < bpool.get_balance(erc20_token.address)
    assert dt_percentage_before < bpool.balanceOf(
        publisher_addr
    ) / bpool.total_supply() * bpool.get_balance(erc20_token.address)
    # other users have added liquidity, so the owner of the pool will have lower percentage
    assert pool_shares_before > bpool.balanceOf(publisher_addr) / bpool.total_supply()

    # TODO: Commented because exit_pool contract method removed
    # exit pool dual side with profit for publisher
    # bpool.exit_pool(
    #     pool_amount_in=bpool.balanceOf(publisher_addr),
    #     min_amounts_out=[to_wei(1), to_wei(1)],
    #     from_wallet=publisher_wallet,
    # )
    # assert erc20_token.balanceOf(publisher_addr) > initial_ocean_liq // 2


@pytest.mark.unit
def test_adding_liquidity_for_vesting(
    web3, config, publisher_wallet, publisher_addr, factory_router, side_staking
):
    """Tests adding liquidity does not affect the vesting amount."""
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(1000)
    )
    mint_fake_OCEAN(config)
    initial_ocean_liq = to_wei(200)
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    pmt_collector = erc20_token.get_payment_collector()

    bpool = _deploy_ocean_pool(
        erc20_token=erc20_token,
        factory_router=factory_router,
        config=config,
        web3=web3,
        from_wallet=publisher_wallet,
    )

    dt_balance_before = erc20_token.balanceOf(pmt_collector)

    # add liquidity to the pool & check events properly
    ocean_contract.approve(bpool.address, to_wei(1000000), publisher_wallet)
    tx = bpool.join_swap_extern_amount_in(
        token_amount_in=to_wei(10),
        min_pool_amount_out=to_wei(1),
        from_wallet=publisher_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    join_event = bpool.get_event_log(
        BPool.EVENT_LOG_JOIN,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert join_event[0].args.caller == publisher_addr
    assert join_event[0].args.tokenIn == ocean_contract.address
    assert join_event[0].args.tokenAmountIn == to_wei(10)

    bpt_event = bpool.get_event_log(
        BPool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert bpt_event[0].args.bptAmount  # amount in pool shares
    assert bpool.get_balance(ocean_contract.address) == initial_ocean_liq + to_wei(10)

    # advance 3 blocks to see if available vesting increased
    _advance_blocks(num_blocks=3, from_wallet=publisher_wallet)

    tx_hash = side_staking.get_vesting(erc20_token.address, publisher_wallet)
    vested_amount = side_staking.get_amount_vested_from_event(
        tx_hash=tx_hash, erc20_token=erc20_token, from_wallet=publisher_wallet
    )
    # vesting amount does not show any modifications after adding liquidity
    assert vested_amount == side_staking.get_vesting_amount_so_far(erc20_token.address)
    assert dt_balance_before < erc20_token.balanceOf(pmt_collector)
    assert erc20_token.balanceOf(pmt_collector) == vested_amount


@pytest.mark.unit
def test_removing_liquidity_for_vesting(
    web3, config, publisher_wallet, publisher_addr, factory_router, side_staking
):
    """Tests removing liquidity does not affect the vesting amount."""
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, publisher_wallet, publisher_wallet, cap=to_wei(1000)
    )
    mint_fake_OCEAN(config)
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    pmt_collector = erc20_token.get_payment_collector()

    bpool = _deploy_ocean_pool(
        erc20_token=erc20_token,
        factory_router=factory_router,
        config=config,
        web3=web3,
        from_wallet=publisher_wallet,
    )

    # check if vesting is correct
    dt_balance_before = erc20_token.balanceOf(pmt_collector)

    # remove liquidity to the pool & check events properly
    ocean_contract.approve(bpool.address, to_wei(1000000), publisher_wallet)
    bt_balance_before = bpool.get_balance(ocean_contract.address)
    tx = bpool.exit_swap_pool_amount_in(
        pool_amount_in=to_wei(1),
        min_amount_out=to_wei(2),
        from_wallet=publisher_wallet,
    )
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    exit_event = bpool.get_event_log(
        BPool.EVENT_LOG_EXIT,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert exit_event[0].args.caller == publisher_addr
    assert exit_event[0].args.tokenOut == ocean_contract.address

    bpt_event = bpool.get_event_log(
        BPool.EVENT_LOG_BPT, tx_receipt.blockNumber, web3.eth.block_number, None
    )
    assert bpt_event[0].args.bptAmount  # amount in pool shares
    assert bt_balance_before > bpool.get_balance(ocean_contract.address)

    # advance 3 blocks to see if available vesting increased
    _advance_blocks(num_blocks=3, from_wallet=publisher_wallet)

    tx_hash = side_staking.get_vesting(erc20_token.address, publisher_wallet)
    vested_amount = side_staking.get_amount_vested_from_event(
        tx_hash=tx_hash, erc20_token=erc20_token, from_wallet=publisher_wallet
    )
    # vesting amount does not show any modifications after removing liquidity
    assert vested_amount == side_staking.get_vesting_amount_so_far(erc20_token.address)
    assert dt_balance_before < erc20_token.balanceOf(pmt_collector)
    assert erc20_token.balanceOf(pmt_collector) == vested_amount


def _deploy_ocean_pool(erc20_token, factory_router, config, web3, from_wallet) -> BPool:
    initial_ocean_liq = to_wei(200)
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(factory_router.address, initial_ocean_liq, from_wallet)
    vested_blocks = factory_router.get_min_vesting_period()

    vesting_amount = initial_ocean_liq // 100 * 9
    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=ocean_contract.decimals(),
        vesting_amount=vesting_amount,
        vesting_blocks=vested_blocks,
        base_token_amount=initial_ocean_liq,
        lp_swap_fee_amount=to_wei("0.003"),
        publish_market_swap_fee_amount=to_wei("0.001"),
        ss_contract=get_address_of_type(config, "Staking"),
        base_token_address=ocean_contract.address,
        base_token_sender=from_wallet.address,
        publisher_address=from_wallet.address,
        publish_market_swap_fee_collector=get_address_of_type(
            config, "OPFCommunityFeeCollector"
        ),
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=from_wallet,
    )

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx)
    pool_event = erc20_token.get_event_log(
        ERC721FactoryContract.EVENT_NEW_POOL,
        tx_receipt.blockNumber,
        web3.eth.block_number,
        None,
    )
    assert pool_event[0].args.poolAddress, "Pool not created."

    return BPool(web3, pool_event[0].args.poolAddress)


def _advance_blocks(num_blocks, from_wallet):
    for _ in range(num_blocks - 1):
        # send dummy transactions to increase block count
        send_ether(from_wallet, ZERO_ADDRESS, 1)
