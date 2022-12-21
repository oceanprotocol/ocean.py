<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Main flow

This step is the fun one! In it, you'll publish a data asset, post for free / for sale, dispense it / buy it, and consume it.

We assume you've already (a) [installed Ocean](install.md), and (b) done [local setup](setup-local.md) or [remote setup](setup-remote.md). This flow works for either one, without any changes between them (!)

Steps in the flow:
1. Alice publishes dataset
2. Bob gets access to the dataset (faucet, priced, etc)
3. Bob consumes the dataset

Let's go!

## 1. Alice publishes dataset

In the same Python console:
```python
#data info
name = "Branin dataset"
url = "https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"

#create data asset
(data_nft, datatoken, ddo) = ocean.assets.create_url_asset(name, url, alice)

#print
print("Just published asset:")
print(f"  data_nft: symbol={data_nft.symbol}, address={data_nft.address}")
print(f"  datatoken: symbol={datatoken.symbol}, address={datatoken.address}")
print(f"  did={ddo.did}")
```

You've now published an Ocean asset!
- `data_nft` is the base (base IP)
- `datatoken` for access by others (licensing)
- `ddo` holding metadata


(For more info, see [Appendix: Publish Details](#appendix-publish-details).)

## 2. Bob gets access to the dataset

Bob wants to consume the dataset that Alice just published. The first step is for Bob to get 1.0 datatokens. Below, we show four possible approaches:
- A & B are when Alice is in contact with Bob. She can mint directly to him, or mint to herself and transfer to him.
- C is when Alice wants to share access for free, to anyone
- D is when Alice wants to sell access

In the same Python console:
```python
#Approach A: Alice mints datatokens to Bob
datatoken.mint(bob, to_wei(1), {"from": alice})

#Approach B: Alice mints for herself, and transfers to Bob
datatoken.mint(alice, to_wei(1), {"from": alice})
datatoken.transfer(bob, to_wei(1), {"from": alice})

#Approach C: Alice posts for free, via a faucet; Bob requests & gets
datatoken.create_dispenser({"from": alice})
datatoken.dispense(to_wei(1), {"from": bob})

#Approach D: Alice posts for sale; Bob buys
# D.1 Alice creates exchange
price = to_wei(100)
exchange = datatoken.create_exchange(price, OCEAN.address, {"from": alice})

# D.2 Alice makes 100 datatokens available on the exchange
datatoken.mint(alice, to_wei(100), {"from": alice_wallet})
datatoken.approve(exchange.address, to_wei(100), {"from": alice})

# D.3 Bob lets exchange pull the OCEAN needed 
OCEAN_needed = exchange.BT_needed(to_wei(1), consume_market_fee=0)
OCEAN.approve(exchange.address, OCEAN_needed, {"from":bob})

# D.4 Bob buys datatoken
exchange.buy_DT(to_wei(1), consume_market_fee=0, tx_dict={"from": bob})
````

(For more info, see [Appendix: Faucet Details](#appendix-faucet-details) and [Exchange Details](#appendix-exchange-details).)

## 3. Bob consumes the dataset

Bob now has the datatoken for the dataset! Time to download the dataset and use it.

In the same Python console:
```python
# Bob sends a datatoken to the service to get access
order_tx_id = ocean.assets.pay_for_access_service(ddo, bob)

# Bob downloads the file. If the connection breaks, Bob can try again
file_name = ocean.assets.download_asset(ddo, bob, './', order_tx_id)
```

Let's check that the file is downloaded. In a new console:

```console
cd my_project/datafile.did:op:0xAf07...
ls branin.arff
```

(For more info, see [Appendix: Consume Details](#appendix-consume-details).)

## Next step

If you did this readme with _local_ setup, then your next step is [remote setup](setup-remote.md).

If you did this readme with _remote_ setup, then your next step is [C2D](READMEs/c2d-flow.md), where you'll tokenize & monetize an AI algorithm via Compute-to-Data.

Bonus: this README's appendices expand on the steps above with further flexibility.


<h2 id="appendix-publish-details">Appendix: Publish Details</h4>

### Reconstructing Data NFT & Datatoken

Anytime in the future, you can reconstruct your data NFT as an object in Python, via:

```python
from ocean_lib.models.data_nft import DataNFT
config = <like shown elsewhere in READMEs>
data_nft_address = <what you wrote down previously>
data_nft = DataNFT(config, data_nft_address)
```

It's similar for Datatokens. In Python:

```python
from ocean_lib.models.datatoken import Datatoken
config = <like shown elsewhere in READMEs>
datatoken_address = <what you wrote down previously>
datatoken = Datatoken(config, datatoken_address)
```

### Data NFT Interface

Data NFTs implement ERC721 functionality, and ERC725 which extends it.

ERC721:
- Basic spec of a non-fungible token (NFT) 
- Official spec is at [erc721.org](https://erc721.org/)
- Solidity interface is in Ocean contracts repo as [IERC721Template.sol](https://github.com/oceanprotocol/contracts/blob/main/contracts/interfaces/IERC721Template.sol)

ERC725:
- ERC725X is execution, and Y is key-value store
- Official spec is at [eips.ethereum.org](https://eips.ethereum.org/EIPS/eip-725)
- Solidity interface is in Ocean contracts repo as [IERC725X.sol](https://github.com/oceanprotocol/contracts/blob/main/contracts/interfaces/IERC725X.sol) (execution) and [IERC725Y.sol](https://github.com/oceanprotocol/contracts/blob/main/contracts/interfaces/IERC725Y.sol) (key-value store)

The `data_nft` is a Python object of class [DataNFT](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/models/data_nft.py). Thanks to Brownie, the DataNFT class directly exposes the Solidity ERC721 & ERC725 interfaces. This means your `data_nft` object has a Python method for every Solidity method! Thank you, Brownie :)

Besides that, DataNFT implements other Python methods like `create_datatoken()` to improve developer experience. And, [ocean_assets.OceanAssets](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/ocean/ocean_assets.py) and other higher-level Python classes / methods work with DataNFT.

Ocean's architecture allows for >1 implementations of ERC721, each with its own Solidity template and Python class. Here are the templates:
- [ERC721Template.sol](https://github.com/oceanprotocol/contracts/blob/main/contracts/templates/ERC721Template.sol), exposed as Python class `DataNFT`
- (there's just one template so far; we can expect more in the future)

### Datatoken Interface

Datatokens implement ERC20 (fungible token standard) functionality:
- Official spec is at [eips.ethereum.org](https://eips.ethereum.org/EIPS/eip-20)
- Solidity interface is in Ocean contracts repo as [IERC20Template.sol](https://github.com/oceanprotocol/contracts/blob/main/contracts/interfaces/IERC20Template.sol)

Python `datatoken` objects are of Python class [Datatoken](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/models/datatoken.py). Thanks to Brownie, these classes have a Python method for every Solidity method.

Besides that, Datatoken class implements more methods like `start_order()`, `create_exchange()`, and `create_dispenser()` to enhance developer experience.

Ocean's architecture allows for >1 implementations of ERC20, each with its own "template". Here are the templates:
- Template 1: [ERC20Template.sol](https://github.com/oceanprotocol/contracts/blob/main/contracts/templates/ERC20Template.sol), exposed as Python class [Datatoken](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/models/datatoken.py)
- Template 2: [ERC20TemplateEnterprise.sol](https://github.com/oceanprotocol/contracts/blob/main/contracts/templates/ERC20TemplateEnterprise.sol), exposed as Python class [DatatokenEnterprise](https://github.com/oceanprotocol/ocean.py/blob/main/ocean_lib/models/datatoken_enterprise.py). It inherits from template 1 in Solidity and in Python. It adds new methods: a single tx for "dispense & order", and single tx for "buy and order".
- (we can expect more templates in the future)


### DIDs and DDOs

DDOs get returned in `create()` calls. Think of them as metadata, following a well-defined format.

Let's get more specific. A [DID](https://w3c-ccg.github.io/did-spec/) is a decentralized identifier. A DID Document (DDO) is a JSON blob that holds information about the DID. Given a DID, a resolver will return the DDO of that DID.

An Ocean _asset_ has a DID and DDO, alongside a data NFT and >=0 datatokens. The DDO should include metadata about the asset, and define access in at least one service. Only owners or delegated users can modify the DDO.

DDOs follow a schema - a pre-specified structure of possible metadata fields.

Ocean Aquarius helps in reading, decrypting, and searching through encrypted DDO data from the chain.

[Ocean docs](https://docs.oceanprotocol.com/core-concepts/did-ddo) have further info yet.

### Publish Flexibility

Here's an example similar to the `create()` step above, but exposes more fine-grained control.

In the same python console:
```python
# Specify metadata and services, using the Branin test dataset
date_created = "2021-12-28T10:55:11Z"
metadata = {
    "created": date_created,
    "updated": date_created,
    "description": "Branin dataset",
    "name": "Branin dataset",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# Use "UrlFile" asset type. (There are other options)
from ocean_lib.structures.file_objects import UrlFile
url_file = UrlFile(
    url="https://raw.githubusercontent.com/trentmc/branin/main/branin.arff"
)

# Publish data asset
from ocean_lib.ocean.ocean_assets import DatatokenArguments
_, _, ddo = ocean.assets.create(
    metadata,
    alice,
    datatoken_args=[DatatokenArguments(files=[url_file])],
)
```


### DDO Encryption or Compression

The DDO is stored on-chain. It's encrypted and compressed by default. Therefore it supports GDPR "right-to-be-forgotten" compliance rules by default.

You can control this during create():
- To disable encryption, use `ocean.assets.create(..., encrypt_flag=False)`.
- To disable compression, use `ocean.assets.create(..., compress_flag=False)`.
- To disable both, use `ocean.assets.create(..., encrypt_flag=False, compress_flag=False)`.


### Create _just_ a data NFT

Calling `create()` like above generates a data NFT, a datatoken for that NFT, and a ddo. This is the most common case. However, sometimes you may want _just_ the data NFT, e.g. if using a data NFT as a simple key-value store. Here's how:
```python
from ocean_lib.models.arguments import DataNFTArguments
data_nft = ocean.data_nft_factory.create(DataNFTArguments('NFT1', 'NFT1'), alice)
```

If you call `create()` after this, you can pass in an argument `data_nft_address:string` and it will use that NFT rather than creating a new one.

### Create a datatoken from a data NFT

Calling `create()` like above generates a data NFT, a datatoken for that NFT, and a ddo object. However, we may want a second datatoken. Or, we may have started with _just_ the data NFT, and want to add a datatoken to it. Here's how:

```python
from ocean_lib.models.arguments import DatatokenArguments
datatoken = data_nft.create_datatoken(DatatokenArguments("Datatoken 1", "DT1"), alice)
```

If you call `create()` after this, you can pass in an argument `deployed_datatokens:List[Datatoken]` and it will use those datatokens during creation.

<h2 id="appendix-faucet-details">Appendix: Faucet Details</h4>

### Faucet Flexibility

`create_dispenser()` can take these optional arguments:
- `max_tokens` - maximum number of tokens to dispense. The default is a large number.
- `max_balance` - maximum balance of requester. The default is a large number.

A call with both would look like `create_dispenser({"from": alice}, max_tokens=max_tokens, max_balance=max_balance)`


### Faucet Tips & Tricks

To learn about dispenser status:

```python
status = datatoken.dispenser_status()
print(f"For datatoken {datatoken.address}:")
print(status)
```

It will output something like:
```text
For datatoken 0x92cA723B61CbD933390aA58b83e1F00cedf4ebb6:
DispenserStatus:
  active = True
  owner_address = 0x1234
  is_minter = True
  max_tokens = 1000 (10000000000000000000000 wei)
  max_balance = 10  (100000000000000000000 wei)
  balance = 1
  allowed_swapper = anyone can request
```


<h2 id="appendix-exchange-details">Appendix: Exchange Details</h4>

### Exchange Flexibility

When Alice posted the dataset for sale via `create_exchange()`, she used OCEAN. Alternatively, she could have used H2O, the OCEAN-backed stable asset. Or, she could have used USDC, DAI, RAI, WETH, or other, for a slightly higher fee (0.2% vs 0.1%).


### Exchange Tips & Tricks

Here's how to see all the exchanges that list the datatoken. In the Python console:
```python
exchanges = datatoken.get_exchanges() # list of OneExchange
```

To learn more about the exchange status:

```python
print(exchange.details)
print(exchange.fees_info)
```

It will output something like:
```text
>>> print(exchange.details)
ExchangeDetails: 
  datatoken = 0xdA3cf7aE9b28E1A9B5F295201d9AcbEf14c43019
  base_token = 0x24f42342C7C171a66f2B7feB5c712471bED92A97
  fixed_rate (price) = 1.0 (1000000000000000000 wei)
  active = True
  dt_supply = 99.0 (99000000000000000000 wei)
  bt_supply = 1.0 (1000000000000000000 wei)
  dt_balance = 0.0 (0 wei)
  bt_balance = 1.0 (1000000000000000000 wei)
  with_mint = False
  dt_decimals = 18
  bt_decimals = 18
  owner = 0x02354A1F160A3fd7ac8b02ee91F04104440B28E7

>>> print(exchange.fees_info)
FeesInfo: 
  publish_market_fee = 0.0 (0 wei)
  publish_market_fee_available = 0.0 (0 wei)
  publish_market_fee_collector = 0x02354A1F160A3fd7ac8b02ee91F04104440B28E7
  opc_fee = 0.001 (1000000000000000 wei)
  ocean_fee_available (to opc) = 0.001 (1000000000000000 wei)
```


<h2 id="appendix-consume-details">Appendix: Consume Details</h4>

### About ARFF format

The file is in ARFF format, used by some AI/ML tools. Our example has two input variables (x0, x1) and one output.

```console
% 1. Title: Branin Function
% 3. Number of instances: 225
% 6. Number of attributes: 2

@relation branin

@attribute 'x0' numeric
@attribute 'x1' numeric
@attribute 'y' numeric

@data
-5.0000,0.0000,308.1291
-3.9286,0.0000,206.1783
...
```
