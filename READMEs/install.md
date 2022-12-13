<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->
## Setup
This quickstart describes the required setup to run `ocean.py` flows.

### 1. Prerequisites

-   Linux/MacOS
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5 - Python 3.10.4

### 2. Download barge and run services

Ocean `barge` runs ganache (local blockchain), Provider (data service), and Aquarius (metadata cache).

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start Ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
./start_ocean.sh
```

Now that we have barge running, we can mostly ignore its console while it runs.

### 3. Install ocean.py library

In a *new* console (separate from barge):

```console
# Create your working directory
mkdir my_project
cd my_project

# Initialize virtual environment and activate it. Install artifacts.
python3 -m venv venv
source venv/bin/activate

# Avoid errors for the step that follows
pip3 install wheel

# Install Ocean library. Allow pre-releases to get the latest v4 version.
pip3 install --pre ocean-lib
```

#### Potential issues & workarounds

From the `pip install` step, here are potential issues and workarounds.

- Issue: if you have an Apple M1 processor, `coincurve` and `cryptography` installation may fail due to dependency/compilation issues.
- Workaround: install them individually: `pip3 install coincurve && pip3 install cryptography`


- Issue: if you run MacOS, you may encounter an "Unsupported Architecture" issue.
- Workaround: install including ARCHFLAGS: `ARCHFLAGS="-arch x86_64" pip install ocean-lib`. [[Details](https://github.com/oceanprotocol/ocean.py/issues/486).]

### 4. Configure brownie & network

ocean.py uses brownie to connect to deployed smart contracts. To configure the RPC URLs, gas prices and other settings,
create and fill in a network-config.yml in your `~/.brownie` folder, or copy our (very basic) sample from ocean.py:

```console
mkdir ~/.brownie
cp network-config.sample ~/.brownie/network-config.yaml
```

Please check that you have configured all networks before proceeding. Here is a more complete sample from brownie itself: https://eth-brownie.readthedocs.io/en/v1.6.5/config.html.


### 5. Set envvars

In the same console (or another one with venv activated):
```console
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc
```
