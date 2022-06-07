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

## 2. Encrypt and upload to decentralized storage and HuggingFace

Then in the same python console:
```python

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import PathFile
path_file = PathFile(path="~/weights/netG.pth")

# Encrypt file(s) using provider
encrypted_files = ocean.assets.encrypt_files([path_file])

# Upload encrypted file to decentralized storage 
from ocean_lib.storage_provider.storage_provider import StorageProvider
storage_provider = StorageProvider(config)
response = storage_provider.upload(encrypted_files)

# Upload encrypted file to HuggingFace for better discoverability
from ocean_lib.storage_provider.huggingface_hub import HuggingFaceHub
huggingface = HuggingFaceHub()
repo_url = huggingface.upload(encrypted_files, object_name='dcgan', object_type='model')

# Coming soon: Publish asset on chain

# Coming soon: Download and decrypt (using Provider)

```
