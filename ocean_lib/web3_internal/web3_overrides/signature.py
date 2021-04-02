#
# Copyright 2021 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import codecs

from eth_keys.datatypes import Signature
from eth_keys.utils.numeric import int_to_byte
from eth_keys.utils.padding import pad32
from eth_utils import int_to_big_endian
from ocean_lib.enforce_typing_shim import enforce_types_shim


@enforce_types_shim
class SignatureFix(Signature):

    """
    Hack the Signature class to allow rebuilding of signature with a
    v value of 27 or 28 instead of 0 or 1
    """

    def __init__(self, signature_bytes=None, vrs=None, backend=None) -> None:
        """Initialises SignatureFix object."""
        v, r, s = vrs
        if v == 27 or v == 28:
            v -= 27

        vrs = (v, r, s)
        Signature.__init__(self, signature_bytes, vrs, backend)

    def to_hex_v_hacked(self) -> str:
        # Need the 'type: ignore' comment below because of
        # https://github.com/python/typeshed/issues/300
        return "0x" + codecs.decode(
            codecs.encode(self.to_bytes_v_hacked(), "hex"), "ascii"
        )  # type: ignore

    def to_bytes_v_hacked(self) -> bytes:
        v = self.v
        if v == 0 or v == 1:
            v += 27
        vb = int_to_byte(v)
        rb = pad32(int_to_big_endian(self.r))
        sb = pad32(int_to_big_endian(self.s))
        # FIXME: Enable type checking once we have type annotations in eth_utils
        return b"".join((rb, sb, vb))  # type: ignore
