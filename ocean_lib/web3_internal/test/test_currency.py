#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import Decimal, localcontext

import pytest
from ocean_lib.web3_internal.currency import (
    ETHEREUM_DECIMAL_CONTEXT,
    MAX_ETHER,
    MAX_WEI,
    MIN_ETHER,
    MIN_WEI,
    ether_fmt,
    from_wei,
    pretty_ether,
    pretty_ether_and_wei,
    to_wei,
)


def test_from_wei():
    """Test the from_wei function"""
    assert from_wei(0) == Decimal("0"), "Zero wei should equal zero ether"
    assert from_wei(123456789_123456789) == Decimal(
        "0.123456789123456789"
    ), "Conversion from wei to ether failed."
    assert from_wei(1123456789_123456789) == Decimal(
        "1.123456789123456789"
    ), "Conversion from wei to ether failed."

    assert (
        from_wei(MIN_WEI) == MIN_ETHER
    ), "Conversion from minimum wei to minimum ether failed."

    assert (
        from_wei(MAX_WEI) == MAX_ETHER
    ), "Conversion from maximum wei to maximum ether failed."

    with pytest.raises(ValueError):
        # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
        with localcontext(ETHEREUM_DECIMAL_CONTEXT):
            from_wei(MAX_WEI + 1)

    USDT_DECIMALS = 6
    assert from_wei(0, USDT_DECIMALS) == Decimal(
        "0"
    ), "Zero wei of USDT should equal zero ether of USDT"
    assert from_wei(123456789_123456789, USDT_DECIMALS) == Decimal(
        "0.123456"
    ), "Conversion from wei to ether using decimals failed"
    assert from_wei(1123456789_123456789, USDT_DECIMALS) == Decimal(
        "1.123456"
    ), "Conversion from wei to ether using decimals failed"


def test_to_wei():
    """Test the to_wei function"""
    assert to_wei(Decimal("0")) == 0, "Zero ether (Decimal) should equal zero wei"
    assert to_wei("0") == 0, "Zero ether (string) should equal zero wei"
    assert to_wei(0) == 0, "Zero ether (int) should equal zero wei"
    assert (
        to_wei(Decimal("0.123456789123456789")) == 123456789_123456789
    ), "Conversion from ether (Decimal) to wei failed."
    assert (
        to_wei("0.123456789123456789") == 123456789_123456789
    ), "Conversion from ether (string) to wei failed."
    assert (
        to_wei(1) == 1_000000000_000000000
    ), "Conversion from ether (int) to wei failed."

    assert (
        to_wei("0.1234567891234567893") == 123456789_123456789
    ), "Conversion from ether to wei failed, supposed to round towards 0 (aka. truncate)."
    assert (
        to_wei("0.1234567891234567897") == 123456789_123456789
    ), "Conversion from ether to wei failed, supposed to round towards 0 (aka. truncate)."

    assert (
        to_wei(MIN_ETHER) == MIN_WEI
    ), "Conversion from minimum ether to minimum wei failed."

    assert (
        to_wei(MAX_ETHER) == MAX_WEI
    ), "Conversion from maximum ether to maximum wei failed."

    with pytest.raises(ValueError):
        # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
        with localcontext(ETHEREUM_DECIMAL_CONTEXT):
            to_wei(MAX_ETHER + 1)

    USDT_DECIMALS = 6
    assert (
        to_wei("0", USDT_DECIMALS) == 0
    ), "Zero ether of USDT should equal zero wei of USDT"
    assert (
        to_wei("0.123456789123456789", USDT_DECIMALS) == 123456000_000000000
    ), "Conversion from ether to wei using decimals failed"
    assert (
        to_wei("1.123456789123456789", USDT_DECIMALS) == 1_123456000_000000000
    ), "Conversion from ether to wei using decimals failed"


def test_ether_fmt():
    """Test the ether_fmt function"""
    assert (
        ether_fmt("0") == "0.000000000000000000"
    ), "Should have 18 decimal places, no ticker symbol"
    assert (
        ether_fmt("0.123456789123456789", 6) == "0.123456"
    ), "Should have 6 decimal places, rounded down, no ticker symbol"
    assert (
        ether_fmt("123456789", 0, "OCEAN") == "123,456,789 OCEAN"
    ), "Should have commas, 0 decimal places, OCEAN ticker symbol"
    assert (
        ether_fmt(MIN_ETHER) == "0.000000000000000001"
    ), "Should have 18 decimal places, no ticker symbol"
    assert (
        ether_fmt(MAX_ETHER)
        == "115,792,089,237,316,195,423,570,985,008,687,907,853,269,984,665,640,564,039,457.584007913129639935"
    ), "Should have 78 digits, commas, 18 decimal places, no ticker symbol"

    with pytest.raises(ValueError):
        # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
        with localcontext(ETHEREUM_DECIMAL_CONTEXT):
            assert ether_fmt(MAX_ETHER + 1)


def test_pretty_ether():
    """Test the pretty_ether function.
    assert messages ommited for brevity."""
    assert pretty_ether("-1.23") == "-1.23"
    assert pretty_ether(MIN_ETHER) == "1e-18"
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
    assert pretty_ether(MAX_ETHER) == "1.15e+59"
    with pytest.raises(ValueError):
        # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
        with localcontext(ETHEREUM_DECIMAL_CONTEXT):
            pretty_ether(MAX_ETHER + 1)


def test_pretty_ether_and_wei():
    """Test the pretty_ether_and_wei function."""
    # Test with small value
    assert pretty_ether_and_wei(1) == "1e-18 (1 wei)"

    # Test with out ticker
    assert pretty_ether_and_wei(123456789_123456789) == "0.123 (123456789123456789 wei)"

    # Test with ticker
    assert (
        pretty_ether_and_wei(123456789_123456789_12345, "OCEAN")
        == "12.3K OCEAN (12345678912345678912345 wei)"
    )

    # Test with empty ticker string
    assert (
        pretty_ether_and_wei(123456789_123456789_123456789, "")
        == "123M (123456789123456789123456789 wei)"
    )
