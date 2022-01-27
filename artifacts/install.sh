##
## Copyright 2021 Ocean Protocol Foundation
## SPDX-License-Identifier: Apache-2.0
##
rm -rf $VIRTUAL_ENV/lib/python3.9/site-packages/artifacts/
mkdir ${VIRTUAL_ENV}/lib/python3.9/site-packages/artifacts/

find ./artifacts -name '*.json' -exec cp -prv '{}' ${VIRTUAL_ENV}'/lib/python3.9/site-packages/artifacts/' ';'
