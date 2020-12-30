

# Posthuman : Ocean Marketplace for Pretrained Transformer Models

Posthuman Marketplace is a fork of ocean lib, aimed at implementing the following functionality:
1. Verifiably Training, Evaluating, and utilising models in Zero-Knowledge using Compute-to-Data
2. Reward contributors to training to incentivise large-scale federated training.

Posthuman Marketplace is currently deployed on Rinkeby. The code is complete for the above functionality. Additional functionality will be added in the next two months. Posthuman relies on the huggingface-transformers library for training and inference scripts, and is deployed on a kubernetes V100 cluster.

We've implemented three separate, customized compute-to-data services:

   compute_service_train [with reward mechanism]
   compute_service_inference
   compute_service_evaluate

Which together give Posthuman PoC the following functionality:

   1. Alice publishes a GPT-2 model in a compute to data environment. 
   2. Bob buys datatokens and runs further training on the WikiText-2 dataset, using the train_lm.py algorithim. [compute_service_train]
   3. The updated model (M2)- 
   i) remains on alice's machine;
   ii) is published as an asset on ocean
   iii) Bob is rewarded with datatokens of the newly trained model
   4. Charlie decides to train the model further, purchasing datatokens from Bob, creating demand. 
   5. The second updated model (M3) is likewise published as an asset, and a datatoken reward issued to Charlie [compute_service_train]
   6. Derek finds M3 to be sufficiently trained for his commercial use-case. He buys access to the inference endpoints using the DataTokens in Chalie's Possession, completing the demand loop. [compute_service_inference]
   7. Elena is unsure if the model she is using (M3) is worth what she is paying. She runs an ‘evaluation.py’ C2D request and learns that the model she’s using does indeed have better performance on her dataset than the published SoTA. [compute_service_inference]

This mechanism serves as a basic pay-it-forward method of rewarding intermediate trainers before a model reaches commercial utility. Crucially, all model updates are performed in zero-knowledge to Bob, Charlie and Derek - they simply stake funds on further training and are rewarded with tokens of the updated model.

Alice is the only trusted party in this setup as the model resides on her hardware. In our scenario, Alice represents the PostHuman Marketplace. Posthuman provides the trusted computing backend on which model training and inference occurs. Posthuman is incentivised to protect privacy of each model to ensure all value stays in the ocean ecosystem, and the marketplace as a whole succeeds.

More complex incentive mechanisms can be structured along similar lines - for eg. 50% of datatokens to last trainer, 25% to the one before, 12.5% and so on.


*Computing Cluster:*
We've set up a V100 GPU based kubernetes cluster for optimial efficiency in training and inference from large transformers. We will eventually expand this to 100s of GPUs to support GPT-3 scale models.

*Algorithims:*
We've included versatile training and inference algorithims from huggingface for use on our marketplace. Small modifications to these templates will cover virtually all transformer fine-tuning and inference use cases.


# ocean-lib

`ocean-lib` is a Python library to privately & securely publish, exchange, 
and consume data. With it, you can:
* **Publish** data services: downloadable files or compute-to-data. 
Ocean creates a new [ERC20](https://github.com/ethereum/EIPs/blob/7f4f0377730f5fc266824084188cc17cf246932e/EIPS/eip-20.md) 
datatoken for each data set.
* **Mint** datatokens to allow buying/consuming the data service
* **Consume** datatokens, to access the service
* **Transfer** datatokens to another owner, and **all other ERC20 actions** 
using [web3.py](https://web3py.readthedocs.io/en/stable/examples.html#working-with-an-erc20-token-contract) etc.
* **Price** datatokens in terms of OCEAN tokens by creating a Balancer pool of `datatoken <> OCEAN`
* **Stake** OCEAN tokens on specific datatokens (by adding OCEAN liquidity into a datatoken Balancer pool)
* Buy datatokens from available Balancer pools or from fixed price exchange if available
* And much more ...


`ocean-lib` is part of the [Ocean Protocol](https://www.oceanprotocol.com) toolset.

## Quick Install

```pip install ocean-lib```

## Quickstart

### 1. Basic setup

[Use this guide](READMEs/setup.md) to connect to Ethereum network and Ocean service providers, configure your Ethereum account / private key, and publish your very first datatoken.

### 2. Get an overview of ocean-lib

[Here's](READMEs/overview.md) a short description of key ocean-lib modules and functions.

### 3. Quickstart marketplace flow

[This quickstart](READMEs/marketplace_flow.md) describes how to publish data assets as datatokens (including metadata), post the datatokens to a marketplace, buy datatokens, and consume datatokens (including download).

## For ocean-lib Developers

If you want to further develop ocean-lib, then [please go here](READMEs/developers.md).

## License

```
Copyright ((C)) 2020 Ocean Protocol Foundation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```
