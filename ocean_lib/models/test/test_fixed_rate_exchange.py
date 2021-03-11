#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from ocean_lib.models.data_token import DataToken
from ocean_lib.models.fixed_rate_exchange import FixedRateExchange
from ocean_lib.ocean.util import from_base_18, to_base_18
from web3.exceptions import ValidationError


def run_failing_tx(contract, fn, *args):
    """Helper function for testing a failed transfer."""
    try:
        tx_id = fn(*args)
        return contract.get_tx_receipt(tx_id).status
    except ValueError:
        return 0
    except ValidationError:
        return 0


def test_fixed_rate_exchange(
    alice_ocean, alice_wallet, T1, bob_wallet, T2, contracts_addresses
):
    """Tests for fixed rate exchange.

    tests:
        create
        generateExchangeId
        getExchange
        getExchanges
        getNumberOfExchanges
        get_base_token_quote
        buy_data_token

    """
    base_unit = to_base_18(1.0)
    fixed_ex = FixedRateExchange(contracts_addresses[FixedRateExchange.CONTRACT_NAME])
    num_ex = fixed_ex.getNumberOfExchanges()
    assert num_ex == len(
        fixed_ex.getExchanges()
    ), "num exchanges do not match num of exchange ids."

    ocean_t = alice_ocean.OCEAN_address
    ocn_token = DataToken(ocean_t)
    # owner_wallet = get_ganache_wallet()
    # ocn_token.transfer_tokens(bob_wallet.address, 100, owner_wallet)
    assert ocn_token.token_balance(bob_wallet.address) >= 100, (
        f"bob wallet does not have the expected OCEAN tokens balance, "
        f"got {ocn_token.token_balance(bob_wallet.address)} instead of 100"
    )

    # clear any previous ocean token allowance for the exchange contract
    assert (
        ocn_token.get_tx_receipt(
            ocn_token.approve(fixed_ex.address, 1, bob_wallet)
        ).status
        == 1
    ), "approve failed"
    assert ocn_token.allowance(bob_wallet.address, fixed_ex.address) == 1, ""

    rate = to_base_18(0.1)
    tx_id = fixed_ex.create(ocean_t, T1.address, rate, alice_wallet)
    r = fixed_ex.get_tx_receipt(tx_id)
    assert r.status == 1, f"create fixed rate exchange failed: TxId {tx_id}."

    ex_id = fixed_ex.generateExchangeId(ocean_t, T1.address, alice_wallet.address).hex()
    ex_data = fixed_ex.getExchange(ex_id)
    expected_values = (alice_wallet.address, T1.address, ocean_t, rate, True, 0)
    assert ex_data == expected_values, (
        f"fixed rate exchange {ex_id} with values {ex_data} "
        f"does not match the expected values {expected_values}"
    )

    assert (
        fixed_ex.getNumberOfExchanges() == num_ex + 1
    ), f"Number of exchanges does not match, expected {num_ex+1} got {fixed_ex.getNumberOfExchanges()}."

    ###################
    # Test quote and buy datatokens
    amount = to_base_18(10.0)  # 10 data tokens
    base_token_quote = fixed_ex.get_base_token_quote(ex_id, amount)
    # quote = from_base_18(base_token_quote)
    assert base_token_quote == (
        amount * rate / base_unit
    ), f"quote does not seem correct: expected {amount*rate/base_unit}, got {base_token_quote}"
    assert from_base_18(base_token_quote) == 1.0, ""
    # buy without approving OCEAN tokens, should fail
    assert (
        run_failing_tx(fixed_ex, fixed_ex.buy_data_token, ex_id, amount, bob_wallet)
        == 0
    ), (
        f"buy_data_token/swap on EX {ex_id} is expected to fail but did not, "
        f"maybe the FixedRateExchange is already approved as spender for bob_wallet."
    )
    # approve ocean tokens, buying should still fail because datatokens are not approved by exchange owner
    assert (
        ocn_token.get_tx_receipt(
            ocn_token.approve(fixed_ex.address, base_token_quote, bob_wallet)
        ).status
        == 1
    ), "approve failed"
    assert (
        run_failing_tx(fixed_ex, fixed_ex.buy_data_token, ex_id, amount, bob_wallet)
        == 0
    ), (
        f"buy_data_token/swap on EX {ex_id} is expected to fail but did not, "
        f"maybe the FixedRateExchange is already approved as spender for bob_wallet."
    )

    # approve data token, now buying should succeed
    assert (
        T1.get_tx_receipt(T1.approve(fixed_ex.address, amount, alice_wallet)).status
        == 1
    ), "approve failed"
    assert (
        ocn_token.allowance(bob_wallet.address, fixed_ex.address) == base_token_quote
    ), ""
    tx_id = fixed_ex.buy_data_token(ex_id, amount, bob_wallet)
    r = fixed_ex.get_tx_receipt(tx_id)
    assert (
        r.status == 1
    ), f"buy_data_token/swap on EX {ex_id} failed with status 0: amount {amount}."
    # verify bob's datatokens balance
    assert T1.balanceOf(bob_wallet.address) == amount, (
        f"bobs datatoken balance is not right, "
        f"should be {amount}, got {T1.balanceOf(bob_wallet.address)}"
    )
    assert ocn_token.allowance(bob_wallet.address, fixed_ex.address) == 0, ""

    #####################
    # create another ex then do more tests
    rate2 = to_base_18(0.8)
    tx_id = fixed_ex.create(ocean_t, T2.address, rate2, alice_wallet)
    r = fixed_ex.get_tx_receipt(tx_id)
    assert r.status == 1, f"create fixed rate exchange failed: TxId {tx_id}."

    assert fixed_ex.getNumberOfExchanges() == num_ex + 2, (
        f"Number of exchanges does not match, "
        f"expected {num_ex+2} got {fixed_ex.getNumberOfExchanges()}."
    )

    t2_ex_id = fixed_ex.generateExchangeId(
        ocean_t, T2.address, alice_wallet.address
    ).hex()
    exchange_ids = {ti.hex() for ti in fixed_ex.getExchanges()}
    assert ex_id in exchange_ids, "exchange id not found."
    assert t2_ex_id in exchange_ids, "exchange id not found."

    ##############################
    # test activate/deactivate
    assert fixed_ex.isActive(ex_id) is True, f"exchange {ex_id} is not active."
    assert fixed_ex.isActive(t2_ex_id) is True, f"exchange {t2_ex_id} is not active."

    assert (
        run_failing_tx(fixed_ex, fixed_ex.deactivate, t2_ex_id, bob_wallet) == 0
    ), f"exchange {t2_ex_id} deactivate (using bob_wallet) should fail but did not."

    assert (
        fixed_ex.get_tx_receipt(fixed_ex.deactivate(t2_ex_id, alice_wallet)).status == 1
    ), f"exchange {t2_ex_id} deactivate failed."
    assert (
        fixed_ex.isActive(t2_ex_id) is False
    ), f"exchange {t2_ex_id} is active, but it should be deactivated."

    ###################################
    # try buying from deactivated ex
    amount = to_base_18(4.0)  # num data tokens
    base_token_quote = fixed_ex.get_base_token_quote(
        t2_ex_id, amount
    )  # num base token (OCEAN tokens
    assert base_token_quote == (
        amount * rate2 / base_unit
    ), f"quote does not seem correct: expected {amount*rate2/base_unit}, got {base_token_quote}"
    ocn_token.get_tx_receipt(
        ocn_token.approve(fixed_ex.address, base_token_quote, bob_wallet)
    )
    # buy should fail (deactivated exchange)
    assert (
        run_failing_tx(fixed_ex, fixed_ex.buy_data_token, t2_ex_id, amount, bob_wallet)
        == 0
    ), (
        f"buy_data_token/swap on EX {t2_ex_id} is expected to fail but did not, "
        f"maybe the FixedRateExchange is already approved as spender for bob_wallet."
    )
    assert (
        ocn_token.allowance(bob_wallet.address, fixed_ex.address) == base_token_quote
    ), ""
    assert (
        fixed_ex.get_tx_receipt(fixed_ex.activate(t2_ex_id, alice_wallet)).status == 1
    ), f"exchange {t2_ex_id} deactivate failed."
    assert (
        fixed_ex.isActive(t2_ex_id) is True
    ), f"exchange {t2_ex_id} is not active, but it should be."

    ##############################
    # buy should still fail as datatokens are not approved to spend by the exchange contract
    assert (
        run_failing_tx(fixed_ex, fixed_ex.buy_data_token, t2_ex_id, amount, bob_wallet)
        == 0
    ), (
        f"buy_data_token/swap on EX {t2_ex_id} is expected to fail but did not, "
        f"maybe the FixedRateExchange is already approved as spender for bob_wallet."
    )

    # now buy tokens should succeed
    assert (
        T2.get_tx_receipt(T2.approve(fixed_ex.address, amount * 3, alice_wallet)).status
        == 1
    ), "approve failed"
    assert (
        fixed_ex.get_tx_receipt(
            fixed_ex.buy_data_token(t2_ex_id, amount, bob_wallet)
        ).status
        == 1
    ), f"buy_data_token/swap on EX {ex_id} failed, "
    assert ocn_token.allowance(bob_wallet.address, fixed_ex.address) == 0, ""

    # approve again for another purchase
    ocn_token.get_tx_receipt(
        ocn_token.approve(fixed_ex.address, base_token_quote, bob_wallet)
    )
    assert (
        run_failing_tx(
            fixed_ex, fixed_ex.buy_data_token, t2_ex_id, to_base_18(5.0), bob_wallet
        )
        == 0
    ), f"buy_data_token/swap on EX {t2_ex_id} should fail because not enough Ocean tokens are approved by buyer."

    # get new quote for new amount
    base_token_quote = fixed_ex.get_base_token_quote(
        t2_ex_id, to_base_18(5.0)
    )  # num base token (OCEAN tokens
    ocn_token.get_tx_receipt(
        ocn_token.approve(fixed_ex.address, base_token_quote, bob_wallet)
    )
    assert (
        fixed_ex.get_tx_receipt(
            fixed_ex.buy_data_token(t2_ex_id, to_base_18(5.0), bob_wallet)
        ).status
        == 1
    ), f"buy_data_token/swap on EX {t2_ex_id} failed."
    assert ocn_token.allowance(bob_wallet.address, fixed_ex.address) == 0, ""

    ##############################
    # test getRate/setRate
    assert (
        fixed_ex.getRate(t2_ex_id) == rate2
    ), f"T2 exchange rate does not match {rate2}, got {fixed_ex.getRate(t2_ex_id)}"
    assert (
        fixed_ex.getRate(ex_id) == rate
    ), f"T1 exchange rate does not match {rate}, got {fixed_ex.getRate(ex_id)}"
    rate2 = to_base_18(0.75)
    assert (
        fixed_ex.get_tx_receipt(fixed_ex.setRate(t2_ex_id, rate2, alice_wallet)).status
        == 1
    ), "setRate failed."
    assert (
        fixed_ex.getRate(t2_ex_id) == rate2
    ), f"T2 exchange rate does not match {rate2}, got {fixed_ex.getRate(t2_ex_id)}"

    assert (
        run_failing_tx(
            fixed_ex, fixed_ex.setRate, t2_ex_id, to_base_18(0.0), alice_wallet
        )
        == 0
    ), "should not accept rate of Zero."
    assert (
        run_failing_tx(
            fixed_ex, fixed_ex.setRate, t2_ex_id, -to_base_18(0.05), alice_wallet
        )
        == 0
    ), "should not accept a negative rate."
    assert (
        fixed_ex.get_tx_receipt(
            fixed_ex.setRate(t2_ex_id, to_base_18(1000.0), alice_wallet)
        ).status
        == 1
    ), "setRate failed."
