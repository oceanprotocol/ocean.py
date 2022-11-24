<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Creator C2D: Put an Asset and its Algorithm for sale in one step

Publishing an asset requires 3 steps:

1. Create an environment
2. Install Ocean's library and create a python file
3. Select your account and the network
4. Fill the information about your data
5. Fill the information about your algorithm

We do the rest, even authorizing your asset directly for consumption.

At the end of the process you will get:
- Dataset NFT Address: To demonstrate that you are the owner of the asset
- Dataset Token Address: Buyers acquire these tokens to download your asset
- Algorithm NFT Address: To demonstrate that you are the owner of the algorithm
- Algorithm Token Address: Buyers acquire these tokens to use your algorithm


## 1. Create an environment

Windows
```console
# Initialize and activate virtual environment.
python -m venv venv
venv\Scripts\activate
```

Mac and Linux
```console
# Initialize and activate virtual environment.
python3 -m venv venv 
source venv/bin/activate
```


## 2. Install Ocean's library and create file

Open the console
```console
# Install Ocean's library
pip3 install --pre ocean-lib

# Create file
touch publishC2D.py
```


## 3. Fill in the setup, dataset and algorithm fields with your data. After that execute the file

Copy this code in the file and fill in the information about your asset and algorithm
```python
from ocean_lib.processes.C2D_data_and_alg_upload import upload_and_publish_C2D

setup = {
    'PRIVATE_KEY': '', # your wallet private key, make sure you have enough funds
    'network': '', # the network where you want to deploy, for example polygon
}

dataset = {
    'NFT_name': '', # short name of your asset
    'NFT_symbol': '', # symbol of your asset
    'dataset_name': '', # long name of your asset
    'dataset_description': '', # description of your asset, e.g. contents, columns, rows, etc.
    'dataset_type': '', # asset type, e.g., dataset, image, etc.
    'dataset_author': '', # your name or alias
    'dataset_license': '', # license under which it is published, e.g., CC0: PublicDomain
    'dataset_url': '', # url where your data is located

}

algorithm = {
    'ALGO_name': '', # short name of your algorithm
    'ALGO_symbol': '', # symbol of your algorithm
    'name': '', # long name of your algorithm
    'description': '', # description, e.g., what it does, data that needs, what it delivers, etc.
    'type': '', # type of creation, e.g., algorithm, etc.
    'author': '', # your name or alias
    'license': '', # license under which it is published, e.g., CC0: PublicDomain
    'algorithm': {}, # a more detailed description of your algorithm (this needs work)
    'url' : '', # url where your the file where your algorithm is located
}

upload_and_publish_C2D(setup, dataset, algorithm)
```
