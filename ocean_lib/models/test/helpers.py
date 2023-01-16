from brownie.network import web3
from enforce_typing import enforce_types


@enforce_types
def interrogate_blockchain_for_reverts(
    receiver: str, sender: str, value: int, input: str, previous_block: int
) -> tuple:
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
    try:
        web3.eth.call(replay_tx, previous_block)
    except ValueError as err:
        return err.args[0]["data"]["0x"]["error"], err.args[0]["data"]["0x"]["reason"]
