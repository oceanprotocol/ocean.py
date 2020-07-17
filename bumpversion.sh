#!/bin/bash

set -x
set -e

usage(){
  echo "Usage: $0 {major|minor|patch} [--tag]"
  exit 1
}

if ! [ -x "$(command -v bumpversion)" ]; then
  echo 'Error: bumpversion is not installed.' >&2
  exit 1
elif ! git diff-index --quiet HEAD -- >/dev/null 2>&1; then
  echo 'There are local changes in your the git repository. Please commit or stash them before bumping version.' >&2
  exit 1
fi

if [ "$#" -lt 1 ]; then
    echo "Illegal number of parameters"
    usage
elif [[ $1 != 'major' && $1 != 'minor' && $1 != 'patch' ]]; then
    echo 'First argument must be {major|minor|patch}'
    usage
fi

if [[ $2 == '--tag' ]]; then
  if git branch --contains $(git rev-parse --verify HEAD) | grep -E 'master'; then
    bumpversion --tag --commit $1
  else
    echo "Only master tags can be tagged"
    exit 1
  fi
else
  bumpversion --no-tag $1
fi

