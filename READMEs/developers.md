# Developing ocean.py

This README is how to further *develop* ocean.py. (Compare to the quickstarts which show how to *use* it.)
Steps:
1. **Install dependencies**
1. **Run the services**
1. **Test**
1. **Merge** the changes via a PR
1. **Release** 

## Prerequisites

1. Linux/MacOS
2. Docker
3. Python 3.8.5

## 1. Install dependencies

In a console:
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


## 2. Run the services

Use Ocean Barge to run local Ethereum node with Ocean contracts, Aquarius, and Provider.

In a new console:
```console
git clone https://github.com/oceanprotocol/barge
cd barge
./start_ocean.sh
```

(Or, [run services separately](services.md).)

## 3. Test

First, set private key values that the tests will need. These values line up with values inside `start_ocean.sh` above.
```console
export TEST_PRIVATE_KEY1=0xc594c6e5def4bab63ac29eed19a134c130388f74f019bc74b8f4389df2837a58
export TEST_PRIVATE_KEY2=0xef4b441145c1d0f3b4bc6d61d29f5c6e502359481152f869247c7a4244d45209
```

Some tests don't need other services running. Let's run one:
```console
pytest tests/models/test_btoken.py
```

Now you can run all tests since all services are running:
```console
pytest
```

#### Installing the pre-commit hooks (recommended)
Run `pre-commit install` to automatically apply isort (import sorting), flake8 (linting) and black (automatic code formatting) to commits. Black formatting is the standard and is checked as part of pull requests.

## 5. Merge

Merge the changes via a pull request (PR) etc. 

Specifically, [follow this workflow](https://docs.oceanprotocol.com/concepts/contributing/#fix-or-improve-core-software).

## 6. Release

Release for pip etc.

Specifically, [follow the Release Process instructions](../RELEASE_PROCESS.md).
