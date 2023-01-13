from brownie.network import web3


def interrogate_blockchain_for_reverts(
    receiver: str, sender: str, value: int, input: str, previous_block: int
):
    """Interrogates the blockchain from previous block for reverts messages.
    This approach is used due to the fact that reverted transaction do not come
    with a specific reason of failure that can be caught.
    """

    replay_tx = {
        "to": receiver,
        "from": sender,
        "value": value,
        "data": input,
    }
    web3.eth.call(replay_tx, previous_block)
