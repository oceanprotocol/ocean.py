<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Publish & Consume Flow using onchain data source

This quickstart describes a flow to publish & consume onchain data source

Here are the steps:

1.  Setup
2.  Publish dataset
3.  Consume dataset

Let's go through each step.

## 1. Setup

From [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md), do:
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library
- [x] Setup : Set envvars
- [x] Setup : Setup in Python

## 2. Publish dataset

In the same Python console:
```python
#data info

# This contract call uniswap v2 router contract to obtain the amount of USDC to be obtained when 1ETH is used as input.
uniswap_v2_router = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D" #GOERLI
name = "Uniswap v2 function call"
contract_address = uniswap_v2_router
contract_abi = {
    "inputs": [
        {
            "internalType": "uint256",
            "name": "amountIn",
            "type": "uint256"
        },
        {
            "internalType": "address[]",
            "name": "path",
            "type": "address[]"
        }
    ],
    "name": "getAmountsOut",
    "outputs": [
        {
            "internalType": "uint256[]",
                            "name": "amounts",
            "type": "uint256[]"
        }
    ],
    "stateMutability": "view",
    "type": "function"
}

#create asset
(data_nft, datatoken, asset) = ocean.assets.create_onchain_asset(name, contract_address, contract_abi, alice_wallet)
print(f"Just published asset, with did={asset.did}")
```

That's it! You've created a data asset of "SmartContractCall" asset type. It includes a data NFT, a datatoken for the data NFT, and metadata.

## 3.  Consume the dataset

```python
# Alice mints and send datatokens to Bob
to_address = bob_wallet.address
amt_tokens = ocean.to_wei(10)  # just need 1, send more for spare
datatoken.mint(to_address, amt_tokens, alice_wallet)


# userdata: parameters required for the contract call 
WETH = "0xB4FBF271143F4FBf7B91A5ded31805e42b2208d6"  # GOERLI WETH
UNI = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"  # UNI GOERLI
userdata = {
    "amountIn": ocean.to_wei(1),
    "path": [WETH, UNI]
}

# pay for acces to the service
order_tx_id = ocean.assets.pay_for_access_service(
    asset,
    bob_wallet,
    service,
    consume_market_order_fee_address=bob_wallet.address,
    consume_market_order_fee_token=datatoken.address,
    consume_market_order_fee_amount=0,
    userdata=userdata
)
print("transaction id", order_tx_id)

# Bob now has access! 
file_path = ocean.assets.download_asset(
    asset=asset,
    consumer_wallet=bob_wallet,
    destination='./',
    order_tx_id=order_tx_id,
    service=service,
    userdata=userdata
)

```
That's it. Bob can now read the data from the file stored in his local drive.