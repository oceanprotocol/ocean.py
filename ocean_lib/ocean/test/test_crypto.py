#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from enforce_typing import enforce_types

from ocean_lib.ocean import crypto


@enforce_types
def test_symkey():
    base_str = "foo"
    symkey = crypto.calc_symkey(base_str)
    assert isinstance(symkey, str)
    wrong_symkey = crypto.calc_symkey("testwrong")
    assert wrong_symkey != symkey, "NOK : wrong_sym_key is the same as sym_key"


@enforce_types
def test_sym_encrypt_decrypt():
    symkey = crypto.calc_symkey("1234")

    value = "hello there"
    value_enc = crypto.sym_encrypt(value, symkey)
    assert value_enc != value

    value2 = crypto.sym_decrypt(value_enc, symkey)
    assert value2 == value


@enforce_types
def test_asym_encrypt_decrypt(alice):
    privkey = alice._private_key.hex()  # str
    pubkey = crypto.calc_pubkey(privkey)  # str

    value = "hello there"
    value_enc = crypto.asym_encrypt(value, pubkey)
    assert value_enc != value

    value2 = crypto.asym_decrypt(value_enc, privkey)
    assert value2 == value
