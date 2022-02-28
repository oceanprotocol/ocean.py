<!--
Copyright 2022 Ocean Protocol Foundation
SPDX-License-Identifier: Apache-2.0
-->

# Compute-to-Data (C2D) Flow - More Examples

## Example 1: Image Processing

Run the [c2d-flow README](https://github.com/oceanprotocol/ocean.py/blob/v4main/READMEs/c2d-flow.md)
with the following alterations:

### 3. Alice publishes a dataset

In Step #3 where Alice publishes a dataset, use [lena.png](https://en.wikipedia.org/wiki/Lenna):

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
    url="https://raw.githubusercontent.com/oceanprotocol/ocean.py/issue705-image-processing-c2d-example/tests/resources/images/lena.png"
)
```

### 4. Alice publishes an algorithm

In step #4 where Alice publishes an algorithm, use a standard grayscale algorithm:

```python
# Specify metadata, using the grayscale algorithm
ALGO_date_created = "2021-12-28T10:55:11Z"
ALGO_metadata = {
    "created": ALGO_date_created,
    "updated": ALGO_date_created,
    "description": "grayscale",
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
            "tag": "python-branin", # This image provides all the dependencies of the grayscale.py algorithm
            "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
        },
    }
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
ALGO_url_file = UrlFile(
    url="https://raw.githubusercontent.com/oceanprotocol/ocean.py/issue705-image-processing-c2d-example/tests/resources/algorithms/grayscale.py"
)
```

### Display and Save the Result

Display the image:

```python
from PIL import Image
import io

image = Image.open(io.BytesIO(result))
image.show()
```

Save the image:

```python
f = open('lena-grayscale.png', 'wb')
f.write(result)
f.close()
```

## Example 2: Logistic Regression for Classification

Run the [c2d-flow README](https://github.com/oceanprotocol/ocean.py/blob/v4main/READMEs/c2d-flow.md)
with the following alterations:

### 3. Alice publishes a dataset

In Step #3 where Alice publishes a dataset, use the [Iris Flower Dataset](https://en.wikipedia.org/wiki/Iris_flower_data_set):

```python
# Specify metadata, using the lena.png image
DATA_date_created = "2019-12-28T10:55:11Z"
DATA_metadata = {
    "created": DATA_date_created,
    "updated": DATA_date_created,
    "description": "The Iris flower dataset is a multivariate dataset to train classification algorithms",
    "name": "Iris Flower Dataset",
    "type": "dataset",
    "author": "Ocean Protocol & Raven Protocol",
    "license": "MIT",
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
DATA_url_file = UrlFile(
    url="https://www.openml.org/data/download/61/dataset_61_iris.arff"
)
```

### 4. Alice publishes an algorithm

In step #4 where Alice publishes an algorithm, use a standard grayscale algorithm:

```python
# Specify metadata, using the Logistic Regression algorithm
ALGO_date_created = "2020-01-28T10:55:11Z"
ALGO_metadata = {
    "created": ALGO_date_created,
    "updated": ALGO_date_created,
    "description": "Logistic Regression",
    "name": "Logistic Regression",
    "type": "algorithm",
    "author": "Ocean Protocol & Raven Protocol",
    "license": "MIT",
    "algorithm": {
        "language": "python",
        "format": "docker-image",
        "version": "0.1",
        "container": {
            "entrypoint": "python $ALGO",
            "image": "oceanprotocol/algo_dockers",
            "tag": "python-panda", # This image provides all the dependencies of the logistic_regression.py algorithm
            "checksum": "44e10daa6637893f4276bb8d7301eb35306ece50f61ca34dcab550",
        },
    }
}

# ocean.py offers multiple file types, but a simple url file should be enough for this example
from ocean_lib.structures.file_objects import UrlFile
ALGO_url_file = UrlFile(
    url="https://raw.githubusercontent.com/oceanprotocol/ocean.py/issue705-image-processing-c2d-example/tests/resources/algorithms/logistic_regression.py"
)
```

### Display the Result

Display the result:

```python
import numpy as np
import matplotlib.pyplot as plt

h = 0.02  # step size in the mesh
xx, yy = np.meshgrid(np.arange(3.8, 8.4, h), np.arange(1.5, 4.9, h))

plt.figure(1, figsize=(4, 3))
plt.pcolormesh(xx, yy, model, cmap=plt.cm.Paired)

plt.xlabel("Sepal length")
plt.ylabel("Sepal width")

plt.xlim(xx.min(), xx.max())
plt.ylim(yy.min(), yy.max())

plt.show()
```