#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import logging
from collections import namedtuple
from decimal import ROUND_DOWN, Context, Decimal, localcontext
from typing import Union

from eth_keys import keys
from eth_utils import big_endian_to_int, decode_hex
from ocean_lib.enforce_typing_shim import enforce_types_shim
from ocean_lib.web3_internal.constants import (
    DEFAULT_NETWORK_NAME,
    MAX_UINT256,
    NETWORK_NAME_MAP,
)
from ocean_lib.web3_internal.web3_overrides.signature import SignatureFix
from ocean_lib.web3_internal.web3_provider import Web3Provider

Signature = namedtuple("Signature", ("v", "r", "s"))

logger = logging.getLogger(__name__)


"""decimal.Context tuned to accomadate MAX_WEI.

* precision=78 because there are 78 digits in MAX_WEI (MAX_UINT256).
  Any lower and decimal operations like quantize throw an InvalidOperation error.
* rounding=ROUND_DOWN (towards 0, aka. truncate) to avoid issue where user
  removes 100% from a pool and transaction fails because it rounds up.
"""
ETHEREUM_DECIMAL_CONTEXT = Context(prec=78, rounding=ROUND_DOWN)


"""Constant used to quantize decimal.Decimal to 18 decimal places"""
DECIMAL_PLACES_18 = Decimal(10) ** -18


"""The maximum possible token amount on Ethereum-compatible blockchains, denoted in wei"""
MAX_WEI = MAX_UINT256


"""The maximum possible token amount on Ethereum-compatible blockchains, denoted in ether"""
MAX_WEI_IN_ETHER = Decimal(MAX_WEI).scaleb(-18, context=ETHEREUM_DECIMAL_CONTEXT)


def generate_multi_value_hash(types, values):
    """
    Return the hash of the given list of values.
    This is equivalent to packing and hashing values in a solidity smart contract
    hence the use of `soliditySha3`.

    :param types: list of solidity types expressed as strings
    :param values: list of values matching the `types` list
    :return: bytes
    """
    assert len(types) == len(values)
    return Web3Provider.get_web3().soliditySha3(types, values)


def prepare_prefixed_hash(msg_hash):
    """

    :param msg_hash:
    :return:
    """
    return generate_multi_value_hash(
        ["string", "bytes32"], ["\x19Ethereum Signed Message:\n32", msg_hash]
    )


def add_ethereum_prefix_and_hash_msg(text):
    """
    This method of adding the ethereum prefix seems to be used in web3.personal.sign/ecRecover.

    :param text: str any str to be signed / used in recovering address from a signature
    :return: hash of prefixed text according to the recommended ethereum prefix
    """
    prefixed_msg = f"\x19Ethereum Signed Message:\n{len(text)}{text}"
    return Web3Provider.get_web3().sha3(text=prefixed_msg)


def to_32byte_hex(web3, val):
    """

    :param web3:
    :param val:
    :return:
    """
    return web3.toBytes(val).rjust(32, b"\0")


def split_signature(web3, signature):
    """

    :param web3:
    :param signature: signed message hash, hex str
    :return:
    """
    assert len(signature) == 65, (
        f"invalid signature, " f"expecting bytes of length 65, got {len(signature)}"
    )
    v = web3.toInt(signature[-1])
    r = to_32byte_hex(web3, int.from_bytes(signature[:32], "big"))
    s = to_32byte_hex(web3, int.from_bytes(signature[32:64], "big"))
    if v != 27 and v != 28:
        v = 27 + v % 2

    return Signature(v, r, s)


@enforce_types_shim
def privateKeyToAddress(private_key: str) -> str:
    return Web3Provider.get_web3().eth.account.privateKeyToAccount(private_key).address


@enforce_types_shim
def privateKeyToPublicKey(private_key: str) -> str:
    private_key_bytes = decode_hex(private_key)
    private_key_object = keys.PrivateKey(private_key_bytes)
    return private_key_object.public_key


@enforce_types_shim
def get_network_name(network_id: int = None) -> str:
    """
    Return the network name based on the current ethereum network id.

    Return `ganache` for every network id that is not mapped.

    :param network_id: Network id, int
    :return: Network name, str
    """
    if not network_id:
        network_id = get_network_id()
    return NETWORK_NAME_MAP.get(network_id, DEFAULT_NETWORK_NAME).lower()


@enforce_types_shim
def get_network_id() -> int:
    """
    Return the ethereum network id calling the `web3.version.network` method.

    :return: Network id, int
    """
    return int(Web3Provider.get_web3().version.network)


@enforce_types_shim
def ec_recover(message, signed_message):
    """
    This method does not prepend the message with the prefix `\x19Ethereum Signed Message:\n32`.
    The caller should add the prefix to the msg/hash before calling this if the signature was
    produced for an ethereum-prefixed message.

    :param message:
    :param signed_message:
    :return:
    """
    w3 = Web3Provider.get_web3()
    v, r, s = split_signature(w3, w3.toBytes(hexstr=signed_message))
    signature_object = SignatureFix(vrs=(v, big_endian_to_int(r), big_endian_to_int(s)))
    return w3.eth.account.recoverHash(
        message, signature=signature_object.to_hex_v_hacked()
    )


@enforce_types_shim
def personal_ec_recover(message, signed_message):
    prefixed_hash = add_ethereum_prefix_and_hash_msg(message)
    return ec_recover(prefixed_hash, signed_message)


@enforce_types_shim
def get_ether_balance(address: str) -> int:
    """
    Get balance of an ethereum address.

    :param address: address, bytes32
    :return: balance, int
    """
    return Web3Provider.get_web3().eth.getBalance(address, block_identifier="latest")


@enforce_types_shim
def from_wei(value_in_wei: int) -> Decimal:
    return Web3Provider.get_web3().fromWei(value_in_wei, "ether")


@enforce_types_shim
def to_wei(value_in_ether: Union[Decimal, str]) -> int:
    if isinstance(value_in_ether, str):
        value_in_ether = Decimal(value_in_ether)

    if value_in_ether > MAX_WEI_IN_ETHER:
        raise ValueError("Ether value exceeds MAX_WEI_IN_ETHER.")

    return Web3Provider.get_web3().toWei(
        value_in_ether.quantize(DECIMAL_PLACES_18, context=ETHEREUM_DECIMAL_CONTEXT),
        "ether",
    )


@enforce_types_shim
def ether_fmt(amount_in_ether: Decimal, places: int = 18, ticker: str = "") -> str:
    if amount_in_ether > MAX_WEI_IN_ETHER:
        raise ValueError("Ether value exceeds MAX_WEI_IN_ETHER.")

    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        return (
            moneyfmt(amount_in_ether, places) + " " + ticker
            if ticker
            else moneyfmt(amount_in_ether, places)
        )


@enforce_types_shim
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


@enforce_types_shim
def wei_and_pretty_ether(amount_in_wei: int, ticker: str = "") -> str:
    return "{} ({})".format(amount_in_wei, pretty_ether_from_wei(amount_in_wei, ticker))


@enforce_types_shim
def pretty_ether_from_wei(amount_in_wei: int, ticker: str = "") -> str:
    return pretty_ether(from_wei(amount_in_wei), ticker=ticker)


@enforce_types_shim
def pretty_ether(
    amount_in_ether: Union[Decimal, str], ticker: str = "", trim: bool = True
) -> str:
    """Returns a human readable token amount denoted in ether with optional ticker symbol
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
            if trim:
                return "0 " + ticker if ticker else "0"
            else:
                if exponent == -1:
                    return "0.0 " + ticker if ticker else "0.0"
                else:
                    return "0.00 " + ticker if ticker else "0.00"

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


@enforce_types_shim
def remove_trailing_zeros(value: Decimal) -> Decimal:
    """Returns a Decimal with trailing zeros removed.
    Adapted from https://docs.python.org/3/library/decimal.html#decimal-faq
    """
    # Use ETHEREUM_DECIMAL_CONTEXT to accomodate MAX_WEI_IN_ETHER
    with localcontext(ETHEREUM_DECIMAL_CONTEXT):
        return (
            value.quantize(Decimal(1)).normalize()
            if value == value.to_integral()
            else value.normalize()
        )
