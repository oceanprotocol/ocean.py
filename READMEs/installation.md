<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Installing ocean.py

## Prerequisites

-   Linux/MacOS
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5 - Python 3.10.4


### For local testing: download barge and run services

Ocean `barge` runs ganache (local blockchain), Provider (data service), and Aquarius (metadata cache).

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

# Clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start Ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
# (For speed, we turn off components we don't need for quickstarts, like IPFS)
./start_ocean.sh --no-ipfs --no-dashboard --skip-subgraph-deploy
```

## Install the library

In a new console:

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
pip3 install ocean-lib
```

#### Known issues

- for M1 processors, `coincurve` and `cryptography` installation may fail due to dependency/compilation issues. It is recommended to install them individually, e.g. `pip3 install coincurve && pip3 install cryptography`

- Mac users: if you encounter an "Unsupported Architecture" issue, then install including ARCHFLAGS: `ARCHFLAGS="-arch x86_64" pip install ocean-lib`. [[Details](https://github.com/oceanprotocol/ocean.py/issues/486).]
