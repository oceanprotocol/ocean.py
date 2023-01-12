import pytest


@pytest.mark.unit
def test_fail_transfer_function(consumer_wallet, publisher_wallet, config, data_nft):
    """Tests failure of using the transfer functions."""
    with pytest.raises(
        Exception,
        match="transfer caller is not owner nor approved",
    ):
        data_nft.transferFrom(
            publisher_wallet.address,
            consumer_wallet.address,
            1,
            {"from": consumer_wallet, "required_confs": 0},
        )

    # # Tests for safe transfer as well
    # with pytest.raises(
    #     Exception,
    #     match="transfer caller is not owner nor approved",
    # ):
    #     data_nft.safeTransferFrom(
    #         publisher_wallet.address,
    #         consumer_wallet.address,
    #         1,
    #         {"from": consumer_wallet},
    #     )
