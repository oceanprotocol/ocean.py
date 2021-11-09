##
## Copyright 2021 Ocean Protocol Foundation
## SPDX-License-Identifier: Apache-2.0
##

rm -rf $VIRTUAL_ENV/lib/python3.8/site-packages/artifacts/
mkdir ${VIRTUAL_ENV}/lib/python3.8/site-packages/artifacts/
cp ${HOME}/.ocean/ocean-contracts/artifacts/address.json $VIRTUAL_ENV/lib/python3.8/site-packages/artifacts/address.json

find ${HOME}/.ocean/ocean-contracts/artifacts/contracts -name '*.json' -exec cp -prv '{}' ${VIRTUAL_ENV}'/lib/python3.8/site-packages/artifacts/' ';'