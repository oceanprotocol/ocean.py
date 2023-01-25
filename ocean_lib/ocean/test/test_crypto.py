from enforce_typing import enforce_types

from ocean_lib.ocean import crypto


@enforce_types
def test_symkey():
    base_str = "foo"
    symkey = crypto.calc_symkey(base_str)
    assert isinstance(symkey, str)


@enforce_types
def test_sym_encrypt_decrypt():
    symkey = crypto.calc_symkey("1234")
    
    value = "hello there"
    value_enc = crypto.sym_encrypt(value, symkey)
    assert value_enc != value
    
    value2 = crypto.sym_decrypt(value_enc, symkey)
    assert value2 == value


@enforce_types
def test_calc_pubkey(alice):
    privkey = alice.private_key #str
    pubkey = crypto.calc_pubkey(privkey) # str
    assert pubkey == str(alice.public_key)

    
@enforce_types
def test_asym_encrypt_decrypt(alice):
    privkey = alice.private_key #str
    pubkey = crypto.calc_pubkey(privkey) # str
        
    value = "hello there"
    value_enc = crypto.asym_encrypt(value, pubkey)
    assert value_enc != value
    
    value2 = crypto.asym_decrypt(value_enc, privkey)
    assert value2 == value
    
    
