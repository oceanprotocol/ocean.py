rm -rf $VIRTUAL_ENV/lib/python3.9/site-packages/artifacts/
mkdir ${VIRTUAL_ENV}/lib/python3.9/site-packages/artifacts/
cp -r ../addresses $VIRTUAL_ENV/lib/python3.9/site-packages/artifacts/addresses

find ./ -name '*.json' -exec cp -prv '{}' ${VIRTUAL_ENV}'/lib/python3.9/site-packages/artifacts/' ';'
