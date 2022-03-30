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
from tests.resources.helper_functions import get_address_of_type, deploy_erc721_erc20


@pytest.mark.unit
def test_permission_to_deploy_erc20(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    erc721_factory,
):
    """Tests permissions for ERC721 and check who has ERC20 deployer role."""
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
    permissions = erc721_nft.get_permissions(another_consumer_wallet.address)
    assert permissions[ERC721Permissions.MANAGER] is True
    assert permissions[ERC721Permissions.DEPLOY_ERC20] is False

    erc721_nft.add_to_create_erc20_list(
        consumer_wallet.address, another_consumer_wallet
    )
    erc721_nft.add_to_metadata_list(consumer_wallet.address, another_consumer_wallet)
    erc721_nft.add_to_725_store_list(consumer_wallet.address, another_consumer_wallet)

    permissions = erc721_nft.get_permissions(consumer_wallet.address)

    assert permissions[ERC721Permissions.MANAGER] is False
    assert permissions[ERC721Permissions.DEPLOY_ERC20] is True
    assert permissions[ERC721Permissions.UPDATE_METADATA] is True
    assert permissions[ERC721Permissions.STORE] is True


@pytest.mark.unit
def test_erc20_permissions(
    web3,
    config,
    publisher_wallet,
    consumer_wallet,
    another_consumer_wallet,
    erc721_factory,
):
    """Tests permissions for an ERC20 token."""
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

    erc721_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)
    assert erc721_nft.is_erc20_deployer(consumer_wallet.address) is True

    trx_erc_20 = erc721_nft.create_erc20(
        template_index=1,
        name="ERC20DT1",
        symbol="ERC20DT1Symbol",
        minter=consumer_wallet.address,
        fee_manager=another_consumer_wallet.address,
        publish_market_order_fee_address=publisher_wallet.address,
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
    perms = erc20_token.get_permissions(consumer_wallet.address)
    assert perms[RolesERC20.MINTER] is True
    assert perms[RolesERC20.PAYMENT_MANAGER] is False

    erc20_token.add_payment_manager(consumer_wallet.address, consumer_wallet)
    perms = erc20_token.get_permissions(consumer_wallet.address)
    assert perms[RolesERC20.PAYMENT_MANAGER] is True


@pytest.mark.unit
def test_minting_failed_after_deploying_pool(
    web3, config, publisher_wallet, consumer_wallet, factory_router
):
    """Tests failure to mint new erc20 token even if consumer has the minter role after deploying a pool."""
    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3,
        config,
        erc721_publisher=publisher_wallet,
        erc20_minter=consumer_wallet,
        cap=to_wei(1000),
    )
    erc721_nft.add_to_create_erc20_list(consumer_wallet.address, publisher_wallet)

    # Tests consumer deploys pool and check market fee
    mint_fake_OCEAN(config)
    initial_ocean_liq = to_wei(200)
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(factory_router.address, initial_ocean_liq, consumer_wallet)

    erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=ocean_contract.decimals(),
        vesting_amount=initial_ocean_liq // 100 * 9,
        vesting_blocks=2500000,
        base_token_amount=initial_ocean_liq,
        lp_swap_fee_amount=to_wei("0.003"),
        publish_market_swap_fee_amount=to_wei("0.001"),
        ss_contract=get_address_of_type(config, "Staking"),
        base_token_address=ocean_contract.address,
        base_token_sender=consumer_wallet.address,
        publisher_address=consumer_wallet.address,
        publish_market_swap_fee_collector=get_address_of_type(
            config, "OPFCommunityFeeCollector"
        ),
        pool_template_address=get_address_of_type(config, "poolTemplate"),
        from_wallet=consumer_wallet,
    )

    # consumer fails to mint new erc20 token even if the minter
    perms = erc20_token.get_permissions(consumer_wallet.address)
    assert perms[RolesERC20.MINTER] is True

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.mint(consumer_wallet.address, 1, consumer_wallet)
        assert (
            err.value.args[0]
            == "execution reverted: VM Exception while processing transaction: revert DataTokenTemplate: cap exceeded"
        )


@pytest.mark.unit
def test_pool_creation_fails_for_incorrect_vesting_period(
    web3, config, consumer_wallet, factory_router, side_staking
):
    """Tests failure of the pool creation for a lower vesting period."""

    erc721_nft, erc20_token = deploy_erc721_erc20(
        web3, config, consumer_wallet, consumer_wallet, cap=to_wei(1000)
    )
    initial_ocean_liq = to_wei(200)

    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(factory_router.address, initial_ocean_liq, consumer_wallet)

    with pytest.raises(exceptions.ContractLogicError) as err:
        erc20_token.deploy_pool(
            rate=to_wei(1),
            base_token_decimals=ocean_contract.decimals(),
            vesting_amount=initial_ocean_liq // 100 * 9,
            vesting_blocks=100,
            base_token_amount=initial_ocean_liq,
            lp_swap_fee_amount=to_wei("0.003"),
            publish_market_swap_fee_amount=to_wei("0.001"),
            ss_contract=get_address_of_type(config, "Staking"),
            base_token_address=ocean_contract.address,
            base_token_sender=consumer_wallet.address,
            publisher_address=consumer_wallet.address,
            publish_market_swap_fee_collector=get_address_of_type(
                config, "OPFCommunityFeeCollector"
            ),
            pool_template_address=get_address_of_type(config, "poolTemplate"),
            from_wallet=consumer_wallet,
        )
        assert (
            err.value.args[0]
            == "execution reverted: VM Exception while processing transaction: revert ERC20Template: Vesting period too low. See FactoryRouter.minVestingPeriodInBlocks"
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

    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(factory_router.address, initial_ocean_liq, consumer_wallet)

    tx = erc20_token.deploy_pool(
        rate=to_wei(1),
        base_token_decimals=ocean_contract.decimals(),
        vesting_amount=initial_ocean_liq // 100 * 9,
        vesting_blocks=2500000,
        base_token_amount=initial_ocean_liq,
        lp_swap_fee_amount=to_wei("0.003"),
        publish_market_swap_fee_amount=to_wei("0.001"),
        ss_contract=get_address_of_type(config, "Staking"),
        base_token_address=ocean_contract.address,
        base_token_sender=consumer_wallet.address,
        publisher_address=consumer_wallet.address,
        publish_market_swap_fee_collector=get_address_of_type(
            config, "OPFCommunityFeeCollector"
        ),
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
    assert bpool.opc_fee() == to_wei("0.001")
    assert bpool.get_swap_fee() == to_wei("0.003")
    assert bpool.community_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.community_fee(erc20_token.address) == 0
    assert bpool.publish_market_fee(get_address_of_type(config, "Ocean")) == 0
    assert bpool.publish_market_fee(erc20_token.address) == 0
    assert (
        erc20_token.balanceOf(get_address_of_type(config, "Staking"))
        == MAX_UINT256 - initial_ocean_liq
    )

    # check if the vesting amount is correct
    assert side_staking.get_vesting_amount(erc20_token.address) == vesting_amount

    # check if vesting is correct
    dt_balance_before = erc20_token.balanceOf(erc20_token.get_payment_collector())
    available_vesting_before = side_staking.get_available_vesting(erc20_token.address)

    # advance 100 blocks to see if available vesting increased
    for _ in range(99):
        # send dummy transactions to increase block count (not part of the actual functionality)
        send_ether(consumer_wallet, ZERO_ADDRESS, 1)

    available_vesting_after = side_staking.get_available_vesting(erc20_token.address)
    assert (
        available_vesting_after > available_vesting_before
    ), "Available vesting was not increased!"
    tx_hash = side_staking.get_vesting(erc20_token.address, consumer_wallet)
    vested_amount = side_staking.get_amount_vested_from_event(
        tx_hash=tx_hash, erc20_token=erc20_token, from_wallet=consumer_wallet
    )

    # 100 blocks passed, vesting started block = tx_receipt.blockNumber (deploy pool tx)
    assert vested_amount == int(
        (100 * vesting_amount)
        / (
            side_staking.get_vesting_end_block(erc20_token.address)
            - tx_receipt.blockNumber
        )
    )
    assert vested_amount == side_staking.get_vesting_amount_so_far(erc20_token.address)
    assert dt_balance_before < erc20_token.balanceOf(
        erc20_token.get_payment_collector()
    )
    assert erc20_token.balanceOf(erc20_token.get_payment_collector()) == vested_amount


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
    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(factory_router.address, initial_ocean_liq, publisher_wallet)
    vested_blocks = factory_router.get_min_vesting_period()
    percentages = [0.0002, 0.005, 0.01]
    checkpoint_blocks = list(map(lambda p: int((vested_blocks * p) / 100), percentages))

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
        base_token_sender=publisher_wallet.address,
        publisher_address=publisher_wallet.address,
        publish_market_swap_fee_collector=get_address_of_type(
            config, "OPFCommunityFeeCollector"
        ),
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

    assert pool_event[0].args.ssContract == side_staking.address
    bpool = BPool(web3, pool_event[0].args.poolAddress)
    assert bpool.is_finalized() is True

    # check if vesting is correct
    side_staking.check_vesting_created_event(
        block_number=tx_receipt.blockNumber,
        erc20_token=erc20_token,
        vested_blocks=vested_blocks,
        vesting_amount=vesting_amount,
    )
    dt_balance_before = erc20_token.balanceOf(erc20_token.get_payment_collector())
    available_vesting_before = side_staking.get_available_vesting(erc20_token.address)
    assert available_vesting_before == 0

    # advance checkpoint_block blocks to see if available vesting increased
    counter = 0
    for block in range(checkpoint_blocks[-1]):
        # send dummy transactions to increase block count (not part of the actual functionality)
        send_ether(publisher_wallet, ZERO_ADDRESS, 1)
        if block not in checkpoint_blocks:
            continue
        available_vesting_after = side_staking.get_available_vesting(
            erc20_token.address
        )
        assert (
            available_vesting_after > available_vesting_before
        ), "Available vesting was not increased!"
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
        assert (
            vested_amount
            == int(((block + 1 + counter) * vesting_amount) / vested_blocks)
            - amount_vested_so_far
        )
        # claim tokens after vested blocks
        assert dt_balance_before < erc20_token.balanceOf(
            erc20_token.get_payment_collector()
        )
        assert (
            erc20_token.balanceOf(erc20_token.get_payment_collector())
            == vested_amount + amount_vested_so_far
        )
