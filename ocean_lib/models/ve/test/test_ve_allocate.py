#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
import brownie
import pytest

accounts = None


@pytest.mark.unit
def test_single_allocation(ve_allocate):
    """getveAllocation should return the correct allocation."""
    nftaddr1 = accounts[0].address
    nftaddr2 = accounts[1].address
    nftaddr3 = accounts[2].address

    ve_allocate.setAllocation(100, nftaddr1, 1, {"from": accounts[0]})
    assert ve_allocate.getveAllocation(accounts[0], nftaddr1, 1) == 100

    ve_allocate.setAllocation(25, nftaddr2, 1, {"from": accounts[0]})
    assert ve_allocate.getveAllocation(accounts[0], nftaddr2, 1) == 25

    ve_allocate.setAllocation(50, nftaddr3, 1, {"from": accounts[0]})
    assert ve_allocate.getveAllocation(accounts[0], nftaddr3, 1) == 50

    ve_allocate.setAllocation(0, nftaddr2, 1, {"from": accounts[0]})
    assert ve_allocate.getveAllocation(accounts[0], nftaddr2, 1) == 0


@pytest.mark.unit
def test_single_events(ve_allocate):
    """Test emitted events."""
    nftaddr1 = accounts[1].address
    tx = ve_allocate.setAllocation(100, nftaddr1, 1, {"from": accounts[0]})
    event = ve_allocate.contract.events.AllocationSet().processReceipt(tx)[0]

    assert event.args.sender == accounts[0].address
    assert event.args.nft == accounts[1].address
    assert event.args.chainId == 1
    assert event.args.amount == 100


@pytest.mark.unit
def test_batch_allocation(ve_allocate):
    """getveAllocation should return the correct allocation."""
    nftaddr1 = accounts[0].address
    nftaddr2 = accounts[1].address

    ve_allocate.setBatchAllocation(
        [50, 50], [nftaddr1, nftaddr2], [1, 1], {"from": accounts[0]}
    )
    assert ve_allocate.getveAllocation(accounts[0], nftaddr1, 1) == 50


@pytest.mark.unit
def test_batch_events(ve_allocate):
    """Test emitted events."""
    nftaddr1 = accounts[1].address
    nftaddr2 = accounts[1].address
    tx = ve_allocate.setBatchAllocation(
        [25, 75], [nftaddr1, nftaddr2], [1, 1], {"from": accounts[0]}
    )
    event = ve_allocate.contract.events.AllocationSetMultiple().processReceipt(tx)[0]

    assert event.args.sender == accounts[0].address
    assert event.args.nft == [nftaddr1, nftaddr2]
    assert event.args.chainId == [1, 1]
    assert event.args.amount == [25, 75]


def setup_function():
    global accounts
    accounts = brownie.network.accounts
