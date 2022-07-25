<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Store and Discover Flow

This quickstart describes how to encrypt an asset, store on IPFS and upload to HuggingFace for discoverability. 
Coming soon: Publish asset on chain
Coming soon: Download and decrypt (using Provider)

Here are the steps:

1.  Setup
2.  Alice encrypts and uploads to decentralized storage and HuggingFace

Let's go through each step.

## 1. Setup

### First steps

To get started with this guide, please refer to [data-nfts-and-datatokens-flow](data-nfts-and-datatokens-flow.md) and complete the following steps :
- [x] Setup : Prerequisites
- [x] Setup : Download barge and run services
- [x] Setup : Install the library from v4 sources
- [x] Setup : Set envvars

### Set envvars

We also need to set two additional envvars for using decentalized storage and HuggingFace. To obtain API keys, you will need to create accounts at [web3.storage](https://web3.storage/) or [Estuary](https://docs.estuary.tech/get-invite-key), and [HuggingFace](https://huggingface.co). 

```console
# Set envvars
export STORAGE_KEY=<ADD WEB3.STORAGE OR ESTUARY.TECH KEY HERE>
export HF_KEY=<ADD HUGGINGFACE KEY HERE>

```

## 2. Alice encrypts a dataset and uploads to Filecoin and HuggingFace

Then in the same python console:
```python

object_path = "./hello.txt"
with open(object_path, "rb") as f:
    files = f.read()

# Encrypt file(s) using provider
from ocean_lib.data_provider.data_encryptor import DataEncryptor
encrypt_response = DataEncryptor.encrypt(
    files,
    ocean.config.provider_url,
)
encrypted_files = encrypt_response.content.decode("utf-8")

# Upload encrypted file to decentralized storage 
from ocean_lib.storage_provider.storage_provider import StorageProvider
storage_provider = StorageProvider()
storage_response = storage_provider.upload(encrypted_files.encode("utf-8"))
cid = storage_response.json()['cid']

from ocean_lib.structures.file_objects import IpfsFile
ipfs_file = [IpfsFile(hash=cid)]

# Upload encrypted file to HuggingFace for better discoverability
from ocean_lib.storage_provider.huggingface_hub import HuggingFaceHub
huggingface = HuggingFaceHub()
repo_url = huggingface.upload(encrypted_files.encode("utf-8"), object_name='hello', object_type='dataset')

## 3. Alice publishes an asset

# Specify metadata and services, using the Branin test dataset
metadata = {
    "created": "2021-12-28T10:55:11Z",
    "updated": "2021-12-28T10:55:11Z",
    "description": "hello.txt",
    "name": "hello.txt",
    "type": "dataset",
    "author": "Algovera",
    "license": "CC0: PublicDomain",
}

from ocean_lib.services.service import Service
from ocean_lib.agreements.service_types import ServiceTypes
access_service = Service(
        service_id="0",
        service_type=ServiceTypes.ASSET_ACCESS,
        service_endpoint=ocean.config.provider_url,
        datatoken=datatoken.address,
        files=ipfs_file,
        timeout=0,
    )

asset = ocean.assets.create(
    metadata=metadata,
    publisher_wallet=alice_wallet,
    files=ipfs_file,
    services=[access_service],
    data_nft_address=data_nft.address,
    deployed_datatokens=[datatoken],
)

did = asset.did 

## 4. Bob downloads datasets
The next steps for downloading the dataset are the same as other tutorials. The data file is automatically decrypted by Provider on download.

- Alice creates a datatoken liquidity pool
- Bob buys and downloads data asset 

```
