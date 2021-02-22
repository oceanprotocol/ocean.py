# Publish your first datatoken

## A. Set Ethereum network & node (Rinkeby & Infura)

1. Infura runs hosted Ethereum nodes. Go to https://infura.io and sign up 

2. At Infura site, create a new project

3. Within the project settings page, note your Infura `project id` value. We will use it in the next step.

4. Make the network available as an envvar. In console:
```
export NETWORK_URL=https://rinkeby.infura.io/v3/<your Infura project id>
```

## B. Set Ethereum account and get Rinkeby ETH

1. [Install Metamask to your browser](https://docs.oceanprotocol.com/tutorials/metamask-setup/). This will generate an Ethereum account for you. 

2. [Export the private key from Metamask](https://metamask.zendesk.com/hc/en-us/articles/360015289632-How-to-Export-an-Account-Private-Key). Write it down.

3. [Get Rinkeby ETH from a faucet](https://faucet.rinkeby.io/). Have it sent to  the your Metamask's Ethereum account address.

4. Make your private key available as an envvar. In console:
```
export MY_TEST_KEY=<my_private_key>
```

## C. Install ocean-lib

```console
#create a python virtualenv
python -m venv venv
source venv/bin/activate 

#install!
pip install ocean-lib
```

## D. Publish datatokens

In Python:
```python
import os
from ocean_lib.ocean.ocean import Ocean
from ocean_lib.web3_internal.wallet import Wallet

private_key = os.getenv('MY_TEST_KEY')
config = {'network': os.getenv('NETWORK_URL')}
ocean = Ocean(config)

print("create wallet: begin")
wallet = Wallet(ocean.web3, private_key=private_key)
print(f"create wallet: done. Its address is {wallet.address}")

print("create datatoken: begin. This will take a few seconds, since it's a transaction on Rinkeby.")
datatoken = ocean.create_data_token("Dataset name", "dtsymbol", from_wallet=wallet) 
print(f"created datatoken: done. Its address is {datatoken.address}")
```

If you made it to the end: congrats, you have created your first Ocean datatoken! 🐋

Or, if you got an error like "insufficient funds for gas", it's because your account doesn't have enough ETH to pay for gas. Get more from the faucet linked above.

Follow-on tutorials will flesh things out more.
