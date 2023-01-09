<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Developing ocean.py

This README is how to further _develop_ ocean.py. (Compare to the quickstarts which show how to _use_ it.)
Steps:

1.  **Install dependencies**
2.  **Run barge services**
3.  **Set up contracts**
4.  **Test**
5.  **Merge** the changes via a PR
6.  **Release**

## 1. Install dependencies

### Prerequisites

-   Linux/MacOS
-   Docker, [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5+

### Do Install

In a new console that we'll call the _work_ console (as we'll use it later):

```console
# Clone the repo and enter into it
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py

# Install OS dependencies
sudo apt-get install -y python3-dev gcc python-pytest

# Initialize virtual environment and activate it.
# Make sure your Python version inside the venv is >=3.8.
python3 -m venv venv
source venv/bin/activate

# Install modules in the environment.
pip install -r requirements_dev.txt
```

## 2. Run barge services

In a new console:

```console
#grab repo
git clone https://github.com/oceanprotocol/barge
cd barge

#clean up old containers (to be sure)
docker system prune -a --volumes

# Run barge: start Ganache, Provider, Aquarius; deploy contracts; update ~/.ocean
# The `--with-c2d` option tells barge to include the Compute-to-Data backend
./start_ocean.sh --with-c2d
```

(Or, [run services separately](services.md).)

## 3. Set up contracts

In work console:

```console
#set private keys of two local (ganache) accounts
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc

#needed to mint fake OCEAN for testing with ganache
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
```

Some tests run on Mumbai (e.g. test_mumbai.py), which need fake MATIC. So you also need:
```console
#set private keys of two remote accounts
export REMOTE_TEST_PRIVATE_KEY1=<your remote private key 1>
export REMOTE_TEST_PRIVATE_KEY2=<your remote private key 2>
```

These keys aren't public because bots could eat the fake MATIC. You need to generate your own, and fill them with a faucet; see instructions in remote setup README. Or, [access-protected OPF keys](https://github.com/oceanprotocol/private-keys/blob/main/README.md)).

## 4. Test

In work console:
```console
#run a single test
pytest ocean_lib/models/test/test_data_nft_factory.py::test_start_multiple_order

#run all tests in a file
pytest ocean_lib/models/test/test_data_nft_factory.py

#run all regular tests; see details on pytest markers to select specific suites
pytest
```

The README tests are special. Here's how to run them:
```console
#need to auto-generate READMEs first
mkcodes --github --output tests/generated-readmes/test_{name}.{ext} READMEs

#then run the tests
pytest tests/readmes/test_readmes.py
pytest /tests/integration/remote/test_mumbai_readme.py
```

For envvars that aren't set, `pytest` uses values in `pytest.ini`.


## 5. Merge

Merge the changes via a pull request (PR) etc.

Specifically, [follow this workflow](https://docs.oceanprotocol.com/concepts/contributing/#fix-or-improve-core-software).

## 6. Release

Release for pip etc.

Specifically, [follow the Release Process instructions](./release-process.md).

## 7. Appendix: More tests

### 7.1 Pre-commit hooks

In main console (with venv on):

```console
pre-commit install
```

Now, this will auto-apply isort (import sorting), flake8 (linting) and black (automatic code formatting) to commits. Black formatting is the standard and is checked as part of pull requests.

## 8. Appendix: Contributing to docs

You are welcome to contribute to ocean.py docs and READMEs. For clean markdowns in the READMEs folder, we use the `remark` tool for automatic markdown formatting.
OCEAN has an official repository containing remark settings, so please follow the instructions [here](https://github.com/oceanprotocol/ocean-remark).
