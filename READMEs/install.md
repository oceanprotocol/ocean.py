<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->
# Install Ocean

## Prerequisites

-   Linux/MacOS
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5 - Python 3.10.4

## Install ocean.py library

In a new console:

```console
# Create your working directory
mkdir my_project
cd my_project

# Initialize virtual environment and activate it. Install artifacts.
# Make sure your Python version inside the venv is >=3.8.
python3 -m venv venv
source venv/bin/activate

# Avoid errors for the step that follows
pip install wheel

# Install Ocean library.
pip install ocean-lib
```

## Potential issues & workarounds

Issue: M1 * `coincurve` or `cryptography`
- If you have an Apple M1 processor, `coincurve` and `cryptography` installation may fail due missing packages, which come pre-packaged in other operating systems.
- Workaround: ensure you have `autoconf`, `automake` and `libtool` installed, e.g. using Homebrew or MacPorts.


Issue: MacOS "Unsupported Architecture"
- If you run MacOS, you may encounter an "Unsupported Architecture" issue.
- Workaround: install including ARCHFLAGS: `ARCHFLAGS="-arch x86_64" pip install ocean-lib`. [Details](https://github.com/oceanprotocol/ocean.py/issues/486).

To install ocean-lib using Python 3.11, run `pip install vyper==0.3.7 --ignore-requires-python` before installing ocean-lib.
This is a temporary fix until Vyper has a release declaring dependencies for Python 3.11. We do not directly use Vyper in ocean-lib.

## ocean.py uses Brownie

When you installed Ocean (`ocean-lib` pypi package) above, it included installation of Brownie (`eth-brownie` package).

ocean.py uses Brownie to connect with deployed smart contracts.

Thanks to Brownie, ocean.py treats each Ocean smart contract as a Python class, and each deployed smart contract as a Python object. We love this feature, because it means Python programmers can treat Solidity code as Python code! 🤯

## Next step

You've now installed Ocean, great!

Your next step is to [setup locally](setup-local.md).
