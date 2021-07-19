<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# The ocean.py Release Process

## Step 1: Bump version and push changes

- Create a new local feature branch, e.g. `git checkout -b feature/bumpversion-to-v0.2.5`

- Use the `bumpversion.sh` script to bump the project version. You can execute the script using {major|minor|patch} as first argument to bump the version accordingly:

  - To bump the patch version: `./bumpversion.sh patch`
  - To bump the minor version: `./bumpversion.sh minor`
  - To bump the major version: `./bumpversion.sh major`

- Commit the changes to the feature branch.

  `git commit -m "Bump version <old_version> -> <new_version>"`

- Push the feature branch to GitHub.

  `git push origin feature/bumpversion-to-v0.2.5"`

## Step 2: Merge changes to main branch

- Make a pull request from the just-pushed branch.

- Wait for all the tests to pass!

- Merge the pull request into the `main` branch.

## Step 3: Release

- To make a GitHub release (which creates a Git tag):

  - Go to the ocean.py repo's Releases page <https://github.com/oceanprotocol/ocean.py/releases>
  - Click "Draft a new release".
  - For tag version, put something like `v0.2.5`
  - For release title, put the same value (like `v0.2.5`).
  - For the target, select the `main` branch, or the just-merged commit.
  - Describe the main changes. (In the future, these will come from the changelog.)
  - Click "Publish release".

## Step 4: Verifiy

- Travis will detect the release (a new tag) and run the deployment section of [.travis.yml](.travis.yml), i.e.

  ```yaml
  deploy:
  provider: pypi
  distributions: sdist bdist_wheel
  user: ${PYPI_USER}
  password: ${PYPI_PASSWORD}
  on:
    tags: true
    repo: oceanprotocol/ocean.py
    python: 3.8
  ```

- Go to [ocean.py Travis page](https://travis-ci.com/github/oceanprotocol/ocean.py) and check the Travis job. It should deploy a new release to PyPI.

- Check PyPI for the new release at <https://pypi.org/project/ocean-lib/>

- Go through the [simple quickstart](datatokens-flow.md), ensure it works.
- Go through the [marketplace quickstart](marketplace-flow.md), ensure it works.
