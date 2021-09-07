<!--
Copyright 2021 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# The Aquarius Release Process

Please note that this upgrade does not affect the deployed versions of Aquarius, i.e. http://aquarius.oceanprotocol.com. Contact the Ocean Protocol team for such a deployment.

## Step 0: Update documentation

- Go to https://github.com/oceanprotocol/readthedocs, and follow the steps
- This will update what's shown in https://docs.oceanprotocol.com/references/read-the-docs/aquarius/.

This doesn't actually affect the pip release of the following steps. And if you've just updated READMEs, you can stop after this step if you like.

## Step 1: Bump version and push changes

- Create a new local feature branch, e.g. `git checkout -b feature/bumpversion-to-v3.2.5`

- Use the `bumpversion.sh` script to bump the project version. You can execute the script using {major|minor|patch} as first argument to bump the version accordingly:

  - To bump the patch version: `./bumpversion.sh patch`
  - To bump the minor version: `./bumpversion.sh minor`
  - To bump the major version: `./bumpversion.sh major`

- Commit the changes to the feature branch.

  `git commit -m "Bump version <old_version> -> <new_version>"`

- Push the feature branch to GitHub.

  `git push origin feature/bumpversion-to-v3.2.5"`

## Step 2: Merge changes to main branch

- Make a pull request from the just-pushed branch.

- Wait for all the tests to pass!

- Merge the pull request into the `main` branch.

## Step 3: Release

- To make a GitHub release (which creates a Git tag):

  - Go to the Aquarius repo's Releases page <https://github.com/oceanprotocol/aquarius/releases>
  - Click "Draft a new release".
  - For tag version, put something like `v3.2.5`
  - For release title, put the same value (like `v3.2.5`).
  - For the target, select the `main` branch, or the just-merged commit.
  - Describe the main changes. (In the future, these will come from the changelog.)
  - Click "Publish release".

## Step 4: Verify

- The Github Action will detect the release (a new tag) and run the deployment.
- Check PyPI for the new release at <https://pypi.org/project/ocean-lib/>
