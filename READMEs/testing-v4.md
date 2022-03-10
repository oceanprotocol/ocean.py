<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Quickstart: Test V4

## Prerequisites

-   Linux/MacOS
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

## Run barge services

Ocean `barge` runs ganache (local blockchain), Provider (data service), and Aquarius (metadata cache).

In a new console:

```console
# Grab repo
git clone https://github.com/oceanprotocol/barge
cd barge
git checkout v4

# Clean up old containers (to be sure) if you have used before for V3
# do it once, because there will be different addresses for the contracts
# and temporary, we need to test with the same addresses until contracts
# release (to avoid updates for address.json file permanently).
docker system prune -a --volumes

# Run barge: start ganache for testing the contracts logic only
./start_ocean.sh  --no-dashboard --no-aquarius --no-elasticsearch --no-provider --no-ipfs
```

## Create artifacts/address.json locally

```console
# Grab repo
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py

# Initialize virtual environment and activate it.
python3 -m venv venv
source venv/bin/activate

git checkout issue488-integrate-v4-interfaces
pip3 install -r requirements_dev.txt

# Create a new branch forked by issue488-integrate-v4-interfaces
git checkout -b issue<issue_no>-<description> issue488-integrate-v4-interfaces
git status
```

In `ocean.py/addresses` package, there is `address.json` file which contains different
addresses from your barge output. Please update in `["development"]["v4"]` with the addresses
that you see in barge for each contract key.
Do not commit `address.json`!

## Testing

Use `pytest`, because right now each V4 unit test needs to be tested individually
since we are testing the contracts' logic. See `developers.md` for `pytest` usage,
section 4 called `Test`.
After you tests pass, for code formatting, we use `black`.