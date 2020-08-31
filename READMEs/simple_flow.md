# Quickstart: Simple Flow 

This stripped-down flow shows the essence of Ocean. Just downloading, no metadata.

Here's the steps.
1. Alice publishes a dataset (= publishes a datatoken contract)
1. Alice hosts the dataset
1. Alice mints 100 tokens
1. Alice transfers 1 token to Bob
1. Bob consumes dataset

Let's go through each step.

## 0. Installation

If you haven't installed yet:
```console
pip install ocean-lib
```

## 1. Alice publishes a dataset (= publishes a DataToken contract)

```python
from ocean_lib.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet
from ocean_lib.web3_internal.web3_provider import Web3Provider


config = {
   'network' : 'rinkeby',
}
ocean = Ocean(config)
alice_wallet = Wallet(ocean.web3, private_key='8da4ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f')
assert alice_wallet.key == config['privateKey']

token = ocean.create_data_token(blob='http://localhost:8030/api/v1/services', 'DataToken1', 'DT1', from_wallet=alice_wallet)
dt_address = token.address
```

## 2. Alice hosts the dataset

A local providerService is required, which will serve just one file for this demo.
Let's create the file to be shared:
```
touch /var/mydata/myFolder1/file
```

Run the providerService:
(given that ERC20 contract address from the above is 0x1234)

```
export CONFIG='{"0x1234":"/var/mydata/myFolder1"}'
docker run @oceanprotocol/provider-py
```

## 3. Alice mints 100 tokens

```python
from ocean_lib.models.data_token import DataToken
# From first step above
dt_address = ''
token = DataToken(dt_address)

token.mint(100)
```

## 4. Alice transfers 1 token to Bob

```python
from ocean_lib.models.data_token import DataToken
# From first step above
dt_address = ''
token = DataToken(dt_address)

bob_address = '0x0ecd5f934768df296EfB58802418fD68B53873C0'
token.transfer_tokens(bob_address, 1.0)
```

## 5. Bob consumes dataset

```python
from ocean_lib.ocean import Ocean

dt_address = ''  # From first step
bob_config = {
   'network': 'rinkeby',
}
ocean = Ocean(bob_config)
bob_account = Wallet(get_web3(), private_key='1234ef21b864d2cc526dbdb2a120bd2874c36c9d0a1fb7f8c63d7f7a8b41de8f')

token = ocean.get_data_token(dt_address)
token_factory = ocean.get_dtfactory()
alice_address = token_factory.get_token_minter(token.address)

tx_id = token.transfer_tokens(alice_address, 1, bob_account)
_file_path = token.download(bob_account, tx_id, '~/my-dataset-downloads')
```
