# -*- coding: utf-8 -*-
#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
"""
=========================================================
Logistic Regression 3-class Classifier
=========================================================

Show below is a logistic-regression classifiers decision boundaries on the
first two dimensions (sepal length and width) of the `iris
<https://en.wikipedia.org/wiki/Iris_flower_data_set>`_ dataset. The datapoints
are colored according to their labels.

"""

# Code source: Gaël Varoquaux
# Modified for documentation by Jaques Grobler
# Modified by Ocean Protocol Foundation
# License: BSD 3 clause

import json
import os
import pickle
import sys

# Uncomment if running locally. g not included in oceanprotocol/algo_dockers:python-panda image
# import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn import preprocessing
from sklearn.linear_model import LogisticRegression


def get_input(local=False):
    if local:
        print("Reading local file dataset_61_iris.csv")

        return "dataset_61_iris.csv"

    dids = os.getenv("DIDS", None)

    if not dids:
        print("No DIDs found in environment. Aborting.")
        return

    dids = json.loads(dids)

    for did in dids:
        filename = f"data/inputs/{did}/0"  # 0 for metadata service
        print(f"Reading asset file {filename}.")

        return filename


def run_linear_regression(local=False):
    filename = get_input(local)
    if not filename:
        print("Could not retrieve filename.")
        return

    iris_data = pd.read_csv(filename, header=0)

    X = iris_data.iloc[:, :2]  # we only take the first two features.

    classes = iris_data.iloc[:, -1]  # assume classes are the final column
    le = preprocessing.LabelEncoder()
    le.fit(classes)
    Y = le.transform(classes)

    # Create an instance of Logistic Regression Classifier and fit the data.
    logreg = LogisticRegression(C=1e5)
    logreg.fit(X, Y)

    # Plot the decision boundary. For that, we will assign a color to each
    # point in the mesh [x_min, x_max]x[y_min, y_max].
    x_min, x_max = X.iloc[:, 0].min() - 0.5, X.iloc[:, 0].max() + 0.5
    y_min, y_max = X.iloc[:, 1].min() - 0.5, X.iloc[:, 1].max() + 0.5
    h = 0.02  # step size in the mesh
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    Z = logreg.predict(np.c_[xx.ravel(), yy.ravel()])

    # Put the result into a color plot
    Z = Z.reshape(xx.shape)

    # Uncomment if running locally. matplotlib not included in oceanprotocol/algo_dockers:python-panda image
    # if local:
    #     print("Plotting results")
    #     plot(xx, yy, Z, X, Y)

    filename = "logistic_regression.pickle" if local else "/data/outputs/result"
    with open(filename, "wb") as pickle_file:
        print(f"Pickling results in {filename}")
        pickle.dump(Z, pickle_file)


# Uncomment if running locally. matplotlib not included in oceanprotocol/algo_dockers:python-panda image
# def plot(xx, yy, Z, X, Y):
#     plt.figure(1, figsize=(4, 3))
#     plt.pcolormesh(xx, yy, Z, cmap=plt.cm.Paired)

#     # Plot also the training points
#     plt.scatter(X.iloc[:, 0], X.iloc[:, 1], c=Y, edgecolors="k", cmap=plt.cm.Paired)
#     plt.xlabel("Sepal length")
#     plt.ylabel("Sepal width")

#     plt.xlim(xx.min(), xx.max())
#     plt.ylim(yy.min(), yy.max())
#     plt.xticks(())
#     plt.yticks(())

#     plt.show()


if __name__ == "__main__":
    local = len(sys.argv) == 2 and sys.argv[1] == "local"
    run_linear_regression(local)
