<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->
# Install Ocean

## Prerequisites

-   Linux, MacOS, or Windows
-   [Docker](https://docs.docker.com/engine/install/), [Docker Compose](https://docs.docker.com/compose/install/), [allowing non-root users](https://www.thegeekdiary.com/run-docker-as-a-non-root-user/)
-   Python 3.8.5 - Python 3.10.4, Python 3.11 with some manual alterations

## Install ocean.py library

Ocean.py requires some basic system dependencies which are standard to development images. If you encounter trouble during installation, please make sure you have autoconf, pkg-config and build-essential or their equivalents installed.

In a new console:

```console
# Create your working directory
mkdir my_project
cd my_project

# Initialize virtual environment and activate it. Install artifacts.
# Make sure your Python version inside the venv is >=3.8.
# Anaconda is not fully supported for now, please use venv
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
- Workaround: ensure you have `autoconf`, `automake`, `libtool` and `pkg-config` installed, e.g. using Homebrew or MacPorts.

Issue: Could not build wheels for coincurve
- Reasons for this happening are usually missing dependencies.
- Workaround:
  - make sure you have the OS-level development libraries for building Python packages: `python3-dev` and `build-essential` (install e.g. using apt-get)
  - install the OS-level `libsecp256k1-dev` library (e.g. using apt-get)
  - install pyproject.toml separately, e.g. `pip install pyproject-toml`
  - if ocean-lib installation still fails, install coincurve separately e.g. `pip install coincurve`, then retry

Issue: MacOS "Unsupported Architecture"
- If you run MacOS, you may encounter an "Unsupported Architecture" issue.
- Workaround: install including ARCHFLAGS: `ARCHFLAGS="-arch x86_64" pip install ocean-lib`. [Details](https://github.com/oceanprotocol/ocean.py/issues/486).

Issue: Dependencies and Python 3.11

- ocean.py depends on the `parsimonious` package. In turn, `parsimonious` depends on `getargsspec`, which doesn't support Python 3.11. The workaround: open the package's expressions.py file (e.g. in ./venv/lib/python3.11/site-packages/parsimonious/expressions.py), and change the line `import getfullargspec as getargsspec` instead of the regular import.

## Next step

You've now installed Ocean, great!

Next step is setup:
- [Remote](setup-remote.md) (Win, MacOS, Linux)
- *or* [Local](setup-local.md) (Linux only)

