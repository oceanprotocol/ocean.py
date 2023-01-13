import pytest
from brownie.network import web3


@pytest.mark.unit
def test_fail_transfer_function(consumer_wallet, publisher_wallet, config, data_nft):
    """Tests failure of using the transfer functions."""
    with pytest.raises(
        ValueError,
        match="VM Exception while processing transaction: revert ERC721: transfer caller is not owner nor approved",
    ):
        tx = data_nft.transferFrom(
            publisher_wallet.address,
            consumer_wallet.address,
            1,
            {"from": consumer_wallet, "required_confs": 0},
        )
        tx.wait(1)
        replay_tx = {
            "to": tx.receiver,
            "from": tx.sender.address,
            "value": tx.value,
            "data": tx.input,
        }
        web3.eth.call(replay_tx, tx.block_number - 1)
