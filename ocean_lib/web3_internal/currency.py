#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from decimal import ROUND_DOWN, Context, Decimal, localcontext
from typing import Union

from enforce_typing import enforce_types
from ocean_lib.web3_internal.constants import MAX_UINT256
from web3.main import Web3

"""decimal.Context tuned to accomadate MAX_WEI.

* precision=78 because there are 78 digits in MAX_WEI (MAX_UINT256).
  Any lower and decimal operations like quantize throw an InvalidOperation error.
* rounding=ROUND_DOWN (towards 0, aka. truncate) to avoid issue where user
  removes 100% from a pool and transaction fails because it rounds up.
"""
ETHEREUM_DECIMAL_CONTEXT = Context(prec=78, rounding=ROUND_DOWN)


"""ERC20 tokens usually opt for a decimals value of 18, imitating the
relationship between Ether and Wei."""
DECIMALS_18 = 18


"""The maximum possible token amount on Ethereum-compatible blockchains, denoted in wei"""
MAX_WEI = MAX_UINT256


"""The maximum possible token amount on Ethereum-compatible blockchains, denoted in ether"""
MAX_ETHER = Decimal(MAX_WEI).scaleb(-18, context=ETHEREUM_DECIMAL_CONTEXT)


@enforce_types
def from_wei(token_amount_in_wei: int, decimals: int = DECIMALS_18) -> Decimal:
    """Convert token amount from wei to ether, quantized to the specified number of decimal places."""
    # Coerce to Decimal because Web3.fromWei can return int 0
    token_amount_in_ether = Decimal(Web3.fromWei(token_amount_in_wei, "ether"))
    decimal_places = Decimal(10) ** -abs(decimals)
    return token_amount_in_ether.quantize(
        decimal_places, context=ETHEREUM_DECIMAL_CONTEXT
    )


@enforce_types
def to_wei(
    token_amount_in_ether: Union[Decimal, str, int], decimals: int = DECIMALS_18
) -> int:
    """
    Convert token amount to wei from ether, quantized to the specified number of decimal places
    float input is purposfully not supported
    """
    if isinstance(token_amount_in_ether, str) or isinstance(token_amount_in_ether, int):
        token_amount_in_ether = Decimal(token_amount_in_ether)

    if token_amount_in_ether > MAX_ETHER:
        raise ValueError("Token amount exceeds MAX_ETHER.")

    decimal_places = Decimal(10) ** -abs(decimals)
    return Web3.toWei(
        token_amount_in_ether.quantize(
            decimal_places, context=ETHEREUM_DECIMAL_CONTEXT
        ),
        "ether",
    )


@enforce_types
def ether_fmt(amount_in_ether: Decimal, places: int = 18, ticker: str = "") -> str:
    if amount_in_ether > MAX_ETHER:
        raise ValueError("Token amount exceeds MAX_ETHER.")

    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        return (
            moneyfmt(amount_in_ether, places) + " " + ticker
            if ticker
            else moneyfmt(amount_in_ether, places)
        )


@enforce_types
def moneyfmt(value, places=2, curr="", sep=",", dp=".", pos="", neg="-", trailneg=""):
    """Convert Decimal to a money formatted string.
    Copied from https://docs.python.org/3/library/decimal.html#recipes

    places:  required number of places after the decimal point
    curr:    optional currency symbol before the sign (may be blank)
    sep:     optional grouping separator (comma, period, space, or blank)
    dp:      decimal point indicator (comma or period)
             only specify as blank when places is zero
    pos:     optional sign for positive numbers: '+', space or blank
    neg:     optional sign for negative numbers: '-', '(', space or blank
    trailneg:optional trailing minus indicator:  '-', ')', space or blank

    >>> d = Decimal('-1234567.8901')
    >>> moneyfmt(d, curr='$')
    '-$1,234,567.89'
    >>> moneyfmt(d, places=0, sep='.', dp='', neg='', trailneg='-')
    '1.234.568-'
    >>> moneyfmt(d, curr='$', neg='(', trailneg=')')
    '($1,234,567.89)'
    >>> moneyfmt(Decimal(123456789), sep=' ')
    '123 456 789.00'
    >>> moneyfmt(Decimal('-0.02'), neg='<', trailneg='>')
    '<0.02>'

    """
    q = Decimal(10) ** -places  # 2 places --> '0.01'
    sign, digits, exp = value.quantize(q).as_tuple()
    result = []
    digits = list(map(str, digits))
    build, next = result.append, digits.pop
    if sign:
        build(trailneg)
    for i in range(places):
        build(next() if digits else "0")
    if places:
        build(dp)
    if not digits:
        build("0")
    i = 0
    while digits:
        build(next())
        i += 1
        if i == 3 and digits:
            i = 0
            build(sep)
    build(curr)
    build(neg if sign else pos)
    return "".join(reversed(result))


@enforce_types
def wei_and_pretty_ether(amount_in_wei: int, ticker: str = "") -> str:
    """Returns a formatted token amount denoted in wei and human-readable ether."""
    return "{} ({})".format(
        amount_in_wei, pretty_ether(from_wei(amount_in_wei, ticker))
    )


@enforce_types
def pretty_ether(
    amount_in_ether: Union[Decimal, str], ticker: str = "", trim: bool = True
) -> str:
    """Returns a human-readable token amount denoted in ether with optional ticker symbol
    Set trim=False to include trailing zeros.

    Examples:
    pretty_ether("0", ticker="OCEAN") == "0 OCEAN"
    pretty_ether("0.01234") == "1.23e-2"
    pretty_ether("1234") == "1.23K"
    pretty_ether("12345678") == "12.3M"
    pretty_ether("1000000.000", trim=False) == "1.00M"
    pretty_ether("123456789012") == "123B"
    pretty_ether("1234567890123") == "1.23e+12"
    """
    with localcontext(ETHEREUM_DECIMAL_CONTEXT) as context:
        # Reduce to 3 significant figures
        context.prec = 3
        sig_fig_3 = context.create_decimal(amount_in_ether)

        exponent = sig_fig_3.adjusted()

        if sig_fig_3 == 0:
            return _trim_zero_to_3_digits_or_less(trim, exponent, ticker)

        if exponent >= 12 or exponent < -1:
            # format string handles scaling also, so set scale = 0
            scale = 0
            fmt_str = "{:e}"
        elif exponent >= 9:
            scale = -9
            fmt_str = "{}B"
        elif exponent >= 6:
            scale = -6
            fmt_str = "{}M"
        elif exponent >= 3:
            scale = -3
            fmt_str = "{}K"
        else:
            # scaling and formatting isn't necessary for values between 0 and 1000 (non-inclusive)
            scale = 0
            fmt_str = "{}"

        scaled = sig_fig_3.scaleb(scale)

        if trim:
            scaled = remove_trailing_zeros(scaled)

        return (
            fmt_str.format(scaled) + " " + ticker if ticker else fmt_str.format(scaled)
        )


@enforce_types
def _trim_zero_to_3_digits_or_less(trim: bool, exponent: int, ticker: str) -> str:
    """Returns a string representation of the number zero, limited to 3 digits
    This function exists to reduce the cognitive complexity of pretty_ether
    """
    if trim:
        zero = "0"
    else:
        if exponent == -1:
            zero = "0.0"
        else:
            zero = "0.00"

    return zero + " " + ticker if ticker else zero


@enforce_types
def remove_trailing_zeros(value: Decimal) -> Decimal:
    """Returns a Decimal with trailing zeros removed.
    Adapted from https://docs.python.org/3/library/decimal.html#decimal-faq
    """
    # Use ETHEREUM_DECIMAL_CONTEXT to accomodate MAX_ETHER
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        return (
            value.quantize(Decimal(1)).normalize()
            if value == value.to_integral()
            else value.normalize()
        )
