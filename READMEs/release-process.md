<!--
Copyright 2023 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# The ocean.py Release Process

## Step 0: Update documentation

- If your changes affect what docs.oceanprotocol.com shows, then make changes in the docs repo https://github.com/oceanprotocol/docs and change

## Step 1: Bump version and push changes

- Identify the current version. It's listed at [pypi.org/project/ocean-lib](https://pypi.org/project/ocean-lib/), in this repo in [.bumpversion.cfg](../.bumpversion.cfg), and elsewhere.

- Create a new local feature branch, e.g. `git checkout -b feature/bumpversion-to-v1.2.5`

- Ensure you're in virtual env: `source venv/bin/activate`

- Run `./bumpversion.sh` to bump the project version, as follows:

  - To bump the major version (v**X**.Y.Z): `./bumpversion.sh major`
  - To bump the minor version (vX.**Y**.Z): `./bumpversion.sh minor`
  - To bump the patch version (vX.Y.**Z**): `./bumpversion.sh patch`
  - (Ocean.py follows [semantic versioning](https://semver.org/).)

- Commit the changes to the feature branch. For example:

  `git commit -m "Bump version v1.2.4 -> v1.2.5"`

- Push the feature branch to GitHub.

  `git push origin feature/bumpversion-to-v1.2.5`

## Step 2: Merge changes to main branch

- Make a pull request from the just-pushed branch.

- Wait for all the tests to pass!

- Merge the pull request into the `main` branch.

## Step 3: Release

- To make a GitHub release (which creates a Git tag):

  - Go to the ocean.py repo's Releases page <https://github.com/oceanprotocol/ocean.py/releases>
  - Click "Draft a new release".
  - For tag version, put something like `v1.2.5`
  - For release title, put the same value (like `v1.2.5`).
  - For the target, select the `main` branch, or the just-merged commit.
  - Describe the main changes. (In the future, these will come from the changelog.)
  - Click "Publish release".

## Step 4: Verify

- GitHub Actions will detect the release (a new tag) and run the deployment and publishing to PyPi.

- Check PyPI for the new release at <https://pypi.org/project/ocean-lib/>

