#
# Copyright 2022 Ocean Protocol Foundation
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
    format_units,
    from_wei,
    parse_units,
    pretty_ether,
    pretty_ether_and_wei,
    to_wei,
)

USDT_DECIMALS = 6
MIN_USDT = Decimal("0.000001")
MAX_USDT = Decimal(MAX_WEI).scaleb(-USDT_DECIMALS, context=ETHEREUM_DECIMAL_CONTEXT)

SEVEN_DECIMALS = 7
MIN_SEVEN = Decimal("0.0000001")
MAX_SEVEN = Decimal(MAX_WEI).scaleb(-SEVEN_DECIMALS, context=ETHEREUM_DECIMAL_CONTEXT)


@pytest.mark.unit
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

    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            from_wei(MAX_WEI + 1)


@pytest.mark.unit
def test_format_units():
    """Test the format_units function"""
    assert format_units(0, USDT_DECIMALS) == Decimal("0")
    assert format_units(123456, USDT_DECIMALS) == Decimal("0.123456")
    assert format_units(1_123456, USDT_DECIMALS) == Decimal("1.123456")
    assert format_units(5278_020000, USDT_DECIMALS) == Decimal("5278.02")
    assert format_units(MIN_WEI, USDT_DECIMALS) == MIN_USDT
    assert format_units(MAX_WEI, USDT_DECIMALS) == MAX_USDT

    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_WEI
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            format_units(MAX_WEI + 1, USDT_DECIMALS)

    assert format_units(0, "mwei") == Decimal("0")
    assert format_units(123456, "mwei") == Decimal("0.123456")
    assert format_units(1_123456, "mwei") == Decimal("1.123456")
    assert format_units(5278_020000, "mwei") == Decimal("5278.02")
    assert format_units(MIN_WEI, "mwei") == MIN_USDT
    assert format_units(MAX_WEI, "mwei") == MAX_USDT

    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_WEI
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            format_units(MAX_WEI + 1, "mwei")

    assert format_units(12345, SEVEN_DECIMALS) == Decimal("0.0012345")
    assert format_units(111_1234567, SEVEN_DECIMALS) == Decimal("111.1234567")
    assert format_units(MIN_WEI, SEVEN_DECIMALS) == MIN_SEVEN
    assert format_units(MAX_WEI, SEVEN_DECIMALS) == MAX_SEVEN


@pytest.mark.unit
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

    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            to_wei(MAX_ETHER + 1)


@pytest.mark.unit
def test_parse_units():
    """Test the parse_units function"""
    assert parse_units("0", USDT_DECIMALS) == 0
    assert parse_units("0.123456789123456789", USDT_DECIMALS) == 123456
    assert parse_units("1.123456789123456789", USDT_DECIMALS) == 1_123456
    assert parse_units("5278.02", USDT_DECIMALS) == 5278_020000
    assert parse_units(MIN_USDT, USDT_DECIMALS) == MIN_WEI
    assert parse_units(MAX_USDT, USDT_DECIMALS) == MAX_WEI

    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_USDT
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            parse_units(MAX_USDT + 1, USDT_DECIMALS)

    assert parse_units("0", "mwei") == 0
    assert parse_units("0.123456789123456789", "mwei") == 123456
    assert parse_units("1.123456789123456789", "mwei") == 1_123456
    assert parse_units("5278.02", "mwei") == 5278_020000
    assert parse_units(MIN_USDT, "mwei") == MIN_WEI
    assert parse_units(MAX_USDT, "mwei") == MAX_WEI

    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_USDT
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            parse_units(MAX_USDT + 1, "mwei")

    assert parse_units("0", SEVEN_DECIMALS) == 0
    assert parse_units("0.123456789", SEVEN_DECIMALS) == 1234567
    assert parse_units("1.123456789", SEVEN_DECIMALS) == 1_1234567
    assert parse_units("5278.02", SEVEN_DECIMALS) == 5278_0200000
    assert parse_units(MIN_SEVEN, SEVEN_DECIMALS) == MIN_WEI
    assert parse_units(MAX_SEVEN, SEVEN_DECIMALS) == MAX_WEI


@pytest.mark.unit
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

    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            assert ether_fmt(MAX_ETHER + 1)


@pytest.mark.unit
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
    # Use ETHEREUM_DECIMAL_CONTEXT when performing arithmetic on MAX_ETHER
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        with pytest.raises(ValueError):
            pretty_ether(MAX_ETHER + 1)


@pytest.mark.unit
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
