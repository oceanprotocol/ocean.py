#
# Copyright 2022 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from concurrent.futures import ThreadPoolExecutor
from tests.readmes.test_c2d_flow import c2d_flow_readme


def concurrent_c2d(concurrent_flows: int, duration: int):
    with ThreadPoolExecutor(max_workers=concurrent_flows) as executor:
        for _ in range(concurrent_flows * duration):
            executor.submit(
                c2d_flow_readme,
                "brainin",
                "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/branin.arff",
                "gpr",
                "https://raw.githubusercontent.com/oceanprotocol/c2d-examples/main/branin_and_gpr/gpr.py",
                "python-brain",
            )


def test_concurrent_c2d():
    concurrent_flows_values = [1, 3, 20]
    reps = [3000, 1000, 50]
    for counter in range(len(concurrent_flows_values)):
        concurrent_c2d(concurrent_flows_values[counter], reps[counter])
