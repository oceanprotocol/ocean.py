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
python3 -m venv venv
source venv/bin/activate

# Avoid errors for the step that follows
pip3 install wheel

# Install Ocean library. Allow pre-releases to get the latest v4 version.
pip3 install --pre ocean-lib
```

## Potential issues & workarounds

- Issue: if you have an Apple M1 processor, `coincurve` and `cryptography` installation may fail due to dependency/compilation issues.
- Workaround: install them individually: `pip3 install coincurve && pip3 install cryptography`

- Issue: if you run MacOS, you may encounter an "Unsupported Architecture" issue.
- Workaround: install including ARCHFLAGS: `ARCHFLAGS="-arch x86_64" pip install ocean-lib`. [Details](https://github.com/oceanprotocol/ocean.py/issues/486).

## Next step

You've now installed Ocean, great!

Next up is for you to [configure Brownie](brownie.md), to connect with smart contracts.