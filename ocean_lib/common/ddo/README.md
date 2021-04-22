<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

## DDO Implementation

### Creating a DDO

1.  Generate a DID

```python
from ocean_lib.common.did import DID

did = DID.did()
print(did)
# >> did:op:03e6764478d61ce1d74945b6a99e870dcfdd6048a7caa435afdf7f0c8b4bf6fd
```

2.  Create a DDO

load in the libraries

```python
from did_ddo_lib import OceanDDO
```

Create a DDO object using a DID

```python
ddo = DDO(did)
```

Generate a signature and embedded in the authentication message, return the private key
of the message

```python
private_key = ddo.add_signature(is_embedded = True)
```

Add a service

```python
ddo.add_service('my-service-type', 'https://url-to-service')
```

Add a static proof using the key index 0

```python
ddo.add_proof(0, private_key, signature)
```

Return the DDO as a JSON text

```python
json_text = ddo.as_text()
```

3.  Read a DDO

load in the libraries

```python
from did_ddo_lib import OceanDDO
```

Create a DDO object using JSON text

```python
ddo = OceanDDO(ddo_text = json_text)
```

check to see if it's valid

```python
if ddo.validate():
    print('DDO has a valid structure and data')
```

check to see if there is a static proof included in the DDO

```python
if ddo.is_proof_defined():
    print('DDO has a static proof')
    if ddo.validate_proof():
        print('DDO has a valid proof')
```

Validate a signature and signature text with one of the keys.
As a DDO client, you will need to authenticate the DDO with one of the listed services.

After sending a query to the supporting server, you well get back a `signature text` and `signature value`.

You can then validate the signature against the key_name used to obtain the signature details.

```python
ddo.validate_from_key(key_name, signature_text, signature_value)
```

## DDO Hash

Originally the idea was to use do the following process to generate a DID:

1.  Calculate or get the base id, in our example this will be an assetId.

2.  Create a DDO with an empty DID fields as Ids.

3.  Perform a hash on this partially completed DDO, without hashing the ID fields.

4.  Hash the item from #1 + the DDO hash to give a DID.

5.  Then apply the DID to the Id fields in the DDO.

### Conclusion

At the moment this does not seem to work so well. In theroy we can create the same DDO with or without key Ids, and get the same hash and validation.

So I think maybe the best way is to just hash the JSON text returned from the DDO.as_text() method.
