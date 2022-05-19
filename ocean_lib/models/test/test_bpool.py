#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import pytest
from web3 import exceptions

from ocean_lib.models.erc20_token import ERC20Token
from ocean_lib.web3_internal.currency import to_wei
from tests.resources.helper_functions import get_address_of_type


@pytest.mark.unit
def test_pool_creation_fails_for_incorrect_vesting_period(
    web3, config, publisher_wallet, publish_market_wallet, erc20_token, factory_router
):
    """Tests failure of the pool creation for a lower vesting period."""
    initial_ocean_liq = to_wei(200)

    ocean_contract = ERC20Token(web3=web3, address=get_address_of_type(config, "Ocean"))
    ocean_contract.approve(factory_router.address, initial_ocean_liq, publisher_wallet)

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
            base_token_sender=publisher_wallet.address,
            publisher_address=publisher_wallet.address,
            publish_market_swap_fee_collector=publish_market_wallet.address,
            pool_template_address=get_address_of_type(config, "poolTemplate"),
            from_wallet=publisher_wallet,
        )
        assert (
            err.value.args[0]
            == "execution reverted: VM Exception while processing transaction: revert ERC20Template: Vesting period too low. See FactoryRouter.minVestingPeriodInBlocks"
        )
