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
#clone the repo and enter into it
git clone https://github.com/oceanprotocol/ocean.py
cd ocean.py

#Install OS dependencies
sudo apt-get install -y python3-dev gcc python-pytest

#Initialize virtual environment and activate it.
python -m venv venv
source venv/bin/activate

#Install modules in the environment.
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
#specify config file as an envvar
export OCEAN_CONFIG_FILE=config.ini

#set private keys of two accounts
export TEST_PRIVATE_KEY1=0x8467415bb2ba7c91084d932276214b11a3dd9bdb2930fefa194b666dd8020b99
export TEST_PRIVATE_KEY2=0x1d751ded5a32226054cd2e71261039b65afb9ee1c746d055dd699b1150a5befc

#needed to mint fake OCEAN for testing with ganache
export FACTORY_DEPLOYER_PRIVATE_KEY=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
```

## 4. Test

In work console:
```console
#run a single test
pytest ocean_lib/models/test/test_data_nft_factory.py::test_start_multiple_order

#run all tests in a file
pytest ocean_lib/models/test/test_data_nft_factory.py

#run all regular tests; see details on pytest markers to select specific suites
pytest -m "not slow"

```

For envvars that aren't set, `pytest` uses values in `pytest.ini`.

Bonus: see the [appendix](developers.md#7-appendix-more-tests) for even more tests.

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

### 7.2 Code quality tests

Use [codacy-analysis-cli](https://github.com/codacy/codacy-analysis-cli).

First, install once. In a new console:

```console
curl -L https://github.com/codacy/codacy-analysis-cli/archive/master.tar.gz | tar xvz
cd codacy-analysis-cli-* && sudo make install
```

In main console (with venv on):

```console
#run all tools, plus Metrics and Clones data.
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean

#run tools individually
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean --tool Pylint
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean --tool Prospector
codacy-analysis-cli analyze --directory ~/code/ocean.py/ocean_lib/ocean --tool Bandit
```

You'll get a report that looks like this.

```console
Found [Info] `First line should end with a period (D415)` in ocean_compute.py:50 (Prospector_pep257)
Found [Info] `Missing docstring in __init__ (D107)` in ocean_assets.py:42 (Prospector_pep257)
Found [Info] `Method could be a function` in ocean_pool.py:473 (PyLint_R0201)
Found [Warning] `Possible hardcoded password: ''` in ocean_exchange.py:23 (Bandit_B107)
Found [Metrics] in ocean_exchange.py:
  LOC - 68
  CLOC - 4
  #methods - 6
```

(C)LOC = (Commented) Lines Of Code.

Finally, you can [go here](https://app.codacy.com/gh/oceanprotocol/ocean.py/dashboard) to see results of remotely-run tests. (You may need special permissions.)

## 8. Appendix: Contributing to docs

You are welcome to contribute to ocean.py docs and READMEs. For clean markdowns in the READMEs folder, we use the `remark` tool for automatic markdown formatting.
OCEAN has an official repository containing remark settings, so please follow the instructions [here](https://github.com/oceanprotocol/ocean-remark).

To update the documentation shown in https://docs.oceanprotocol.com/references/read-the-docs/ocean-py/,
go to https://github.com/oceanprotocol/readthedocs, and follow the steps.
