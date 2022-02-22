<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Compute-to-Data (C2D) Flow - More Examples

## Example 1: Image Processing

Run the [c2d-flow README](https://github.com/oceanprotocol/ocean.py/blob/v4main/READMEs/c2d-flow.md)
with the following alterations:

### 3. Alice publishes a dataset

In Step #3 where Alice publishes a dataset, define the dataset like so:

```python
# Specify metadata, using the lena.png image
DATA_date_created = "2021-12-28T10:55:11Z"
DATA_metadata = {
    "created": DATA_date_created,
    "updated": DATA_date_created,
    "description": "lena image",
    "name": "lena",
    "type": "dataset",
    "author": "Trent",
    "license": "CC0: PublicDomain",
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
DATA_url_file = UrlFile(
    url="https://raw.githubusercontent.com/oceanprotocol/ocena.py/v4main/tests/resources/images/lena.png"
)
```

### 4. Alice publishes an algorithm

In step #4 where Alice publishes an algorithm, define the algorithm like so:

```python
# Specify metadata, using the grayscale algorithm
ALGO_date_created = "2021-12-28T10:55:11Z"
ALGO_metadata = {
    "created": ALGO_date_created,
    "updated": ALGO_date_created,
    "description": "gpr",
    "name": "grayscale",
    "type": "algorithm",
    "author": "Trent",
    "license": "CC0: PublicDomain",
    "algorithm": {
        "language": "python",
        "format": "docker-image",
        "version": "0.1",
        "container": {
            "entrypoint": "python $ALGO",
            "image": "oceanprotocol/algo_dockers",
            "tag": "python-grayscale",
            "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
        },
    }
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
ALGO_url_file = UrlFile(
    url="https://raw.githubusercontent.com/oceanprotocol/ocean.py/v4main/tests/resources/algorithms/grayscale.py"
)
```


## Example 2: Logistic Regression for Classification

TODO
logistic regression for classification [blog post](https://medium.com/ravenprotocol/machine-learning-series-using-logistic-regression-for-classification-in-oceans-compute-to-data-18df49b6b165) with both GUI and CLI flows.