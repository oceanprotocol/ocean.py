#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import os
from decimal import Decimal, localcontext

import pytest
from ocean_lib.web3_internal.transactions import (
    cancel_or_replace_transaction,
    send_ether,
)
from ocean_lib.web3_internal.utils import (
    ETHEREUM_DECIMAL_CONTEXT,
    MAX_WEI,
    MAX_WEI_IN_ETHER,
    ether_fmt,
    from_wei,
    generate_multi_value_hash,
    prepare_prefixed_hash,
    pretty_ether,
    to_wei,
    wei_and_pretty_ether,
)


def test_generate_multi_value_hash(alice_address, alice_private_key):
    with pytest.raises(AssertionError):
        generate_multi_value_hash(["more", "types", "than"], ["values"])

    expected = "0x6d59f15c5814d9fddd2e69d1f6f61edd0718e337c41ec74011900c0d736a9fec"
    assert alice_private_key == os.getenv("TEST_PRIVATE_KEY1")
    assert alice_address == "0x66aB6D9362d4F35596279692F0251Db635165871"
    tested = generate_multi_value_hash(["address"], [alice_address]).hex()
    assert tested == expected, "The tested address is not the expected one."


def test_prepare_fixed_hash():
    expected = "0x5662cc8481d004c9aff44f15f3ed133dd54f9cfba0dbf850f69b1cbfc50145bf"
    assert (
        prepare_prefixed_hash("0x0").hex() == expected
    ), "The address is not the expected one."


def test_send_ether(alice_wallet, bob_address):
    assert send_ether(alice_wallet, bob_address, 1), "Send ether was unsuccessful."


def test_cancel_or_replace_transaction(alice_wallet):
    assert cancel_or_replace_transaction(
        alice_wallet, None
    ), "Cancel or replace transaction failed."


def test_from_wei():
    """Test the from_wei function"""
    assert from_wei(0) == Decimal("0"), "Zero wei should equal zero ether"
    assert from_wei(123456789123456789) == Decimal(
        "0.123456789123456789"
    ), "Conversion from wei to ether failed."
    assert from_wei(1123456789123456789) == Decimal(
        "1.123456789123456789"
    ), "Conversion from wei to ether failed."

    assert (
        from_wei(MAX_WEI) == MAX_WEI_IN_ETHER
    ), "Conversion from maximum wei value to ether failed."

    with pytest.raises(ValueError):
        # Use ETHEREUM_DECIMAL_CONTEXT to accomodate MAX_WEI_IN_ETHER
        with localcontext(ETHEREUM_DECIMAL_CONTEXT):
            from_wei(MAX_WEI + 1)


def test_to_wei():
    """Test the to_wei function"""
    assert to_wei(Decimal("0")) == 0, "Zero ether (Decimal) should equal zero wei"
    assert to_wei("0") == 0, "Zero ether (string) should equal zero wei"
    assert (
        to_wei(Decimal("0.123456789123456789")) == 123456789123456789
    ), "Conversion from ether (Decimal) to wei failed."
    assert (
        to_wei("0.123456789123456789") == 123456789123456789
    ), "Conversion from ether (string) to wei failed."

    assert (
        to_wei("0.1234567891234567893") == 123456789123456789
    ), "Conversion from ether to wei failed, supposed to round towards 0 (aka. truncate)."
    assert (
        to_wei("0.1234567891234567897") == 123456789123456789
    ), "Conversion from ether to wei failed, supposed to round towards 0 (aka. truncate)."

    assert (
        to_wei(MAX_WEI_IN_ETHER) == MAX_WEI
    ), "Conversion from ether to maximum wei value failed"

    with pytest.raises(ValueError):
        # Use ETHEREUM_DECIMAL_CONTEXT to accomodate MAX_WEI_IN_ETHER
        with localcontext(ETHEREUM_DECIMAL_CONTEXT):
            to_wei(MAX_WEI_IN_ETHER + 1)


def test_ether_fmt():
    """Test the ether_fmt function"""
    assert (
        ether_fmt(Decimal("0")) == "0.000000000000000000"
    ), "Should have 18 decimal places, no ticker symbol"
    assert (
        ether_fmt(Decimal("0.123456789123456789"), 6) == "0.123456"
    ), "Should have 6 decimal places, rounded down, no ticker symbol"
    assert (
        ether_fmt(Decimal("123456789"), 0, "OCEAN") == "123,456,789 OCEAN"
    ), "Should have commas, 0 decimal places, OCEAN ticker symbol"
    assert (
        ether_fmt(Decimal(MAX_WEI_IN_ETHER))
        == "115,792,089,237,316,195,423,570,985,008,687,907,853,269,984,665,640,564,039,457.584007913129639935"
    ), "Should have 78 digits, commas, 18 decimal places, no ticker symbol"

    with pytest.raises(ValueError):
        # Use ETHEREUM_DECIMAL_CONTEXT to accomodate MAX_WEI_IN_ETHER
        with localcontext(ETHEREUM_DECIMAL_CONTEXT):
            assert ether_fmt(Decimal(MAX_WEI_IN_ETHER + 1))


def test_pretty_ether():
    """Test the pretty_ether function.
    assert messages ommited for brevity."""
    assert pretty_ether("0", ticker="OCEAN") == "0 OCEAN"
    assert pretty_ether("0.000001234") == "1.23e-6"
    assert pretty_ether("0.00001234") == "1.23e-5"
    assert pretty_ether("0.0001234") == "1.23e-4"
    assert pretty_ether("0.001234") == "1.23e-3"
    assert pretty_ether("0.01234") == "1.23e-2"
    assert pretty_ether("0.1234") == "0.123"
    assert pretty_ether("0.1000") == "0.1"
    assert pretty_ether("0") == "0"
    assert pretty_ether("0.000") == "0"
    assert pretty_ether("0.0", trim=False) == "0.0"
    assert pretty_ether("0.00", trim=False) == "0.00"
    assert pretty_ether("0.000", trim=False) == "0.00"
    assert pretty_ether("1") == "1"
    assert pretty_ether("1.000") == "1"
    assert pretty_ether("1.0", trim=False) == "1.0"
    assert pretty_ether("1.000", trim=False) == "1.00"
    assert pretty_ether("1.333") == "1.33"
    assert pretty_ether("1.777") == "1.77"
    assert pretty_ether("12") == "12"
    assert pretty_ether("12.333") == "12.3"
    assert pretty_ether("12.777") == "12.7"
    assert pretty_ether("123") == "123"
    assert pretty_ether("123.333") == "123"
    assert pretty_ether("123.777") == "123"
    assert pretty_ether("1000.000") == "1K"
    assert pretty_ether("1000.000", trim=False) == "1.00K"
    assert pretty_ether("1000.3") == "1K"
    assert pretty_ether("1000.7") == "1K"
    assert pretty_ether("1234") == "1.23K"
    assert pretty_ether("12345") == "12.3K"
    assert pretty_ether("123456") == "123K"
    assert pretty_ether("1000000.000") == "1M"
    assert pretty_ether("1000000.000", trim=False) == "1.00M"
    assert pretty_ether("1234567") == "1.23M"
    assert pretty_ether("12345678") == "12.3M"
    assert pretty_ether("123456789") == "123M"
    assert pretty_ether("1000000000.000") == "1B"
    assert pretty_ether("1000000000.000", trim=False) == "1.00B"
    assert pretty_ether("1234567890") == "1.23B"
    assert pretty_ether("12345678901") == "12.3B"
    assert pretty_ether("123456789012") == "123B"
    assert pretty_ether("1000000000000") == "1e+12"
    assert pretty_ether("1234567890123") == "1.23e+12"
    assert pretty_ether("12345678901234") == "1.23e+13"
    assert pretty_ether(MAX_WEI_IN_ETHER) == "1.15e+59"
    # Use ETHEREUM_DECIMAL_CONTEXT to accomodate MAX_WEI_IN_ETHER
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        assert pretty_ether(MAX_WEI_IN_ETHER + 1) == "1.15e+59"


def test_wei_and_pretty_ether():
    assert (
        wei_and_pretty_ether(123456789123456789, "OCEAN")
        == "123456789123456789 (0.123 OCEAN)"
    )
    assert (
        wei_and_pretty_ether(12345678912345678912345, "OCEAN")
        == "12345678912345678912345 (12.3K OCEAN)"
    )
    assert (
        wei_and_pretty_ether(123456789123456789123456789, "OCEAN")
        == "123456789123456789123456789 (123M OCEAN)"
    )
