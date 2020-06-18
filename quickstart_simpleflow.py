#! ./myenv/bin/python3

# do *not* import brownie, that's too much dependency here
import sys

from ocean_lib import Ocean

ALLOWED_NETWORKS = ['ganache', 'rinkeby', 'mainnet']
ALLOWED_NETWORKS_STR = str(ALLOWED_NETWORKS)[1:-1]


def main():
    network = processArgs()
    runQuickstart(network)


def processArgs():
    # set help message
    help_text = f"""
Run quickstart on simple flow.

Usage: quickstart_simpleflow.py NETWORK
  NETWORK -- one of: {ALLOWED_NETWORKS_STR}
 """

    # ****SET INPUT ARGS****
    # got the right number of args?  If not, output help_text
    num_args = len(sys.argv) - 1
    num_args_needed = 1
    if num_args != num_args_needed:
        print(help_text)
        if num_args > 0:
            print("Got %d argument(s), need %s.\n" % (num_args, num_args_needed))
        sys.exit(0)

    # grab args
    network = sys.argv[1]
    print("Arguments: NETWORK=%s\n" % network)

    # corner cases
    if network not in ALLOWED_NETWORKS:
        print(f"Invalid network. Allowed networks: {ALLOWED_NETWORKS_STR}")
        sys.exit(0)

    return network


def runQuickstart(network):
    # set accounts. For each network, these need ETH with gas.
    alice_private_key = Ocean.confFileValue(network, 'TEST_PRIVATE_KEY1')
    bob_private_key = Ocean.confFileValue(network, 'TEST_PRIVATE_KEY2')
    bob_address = Ocean.privateKeyToAddress(bob_private_key)

    # 1. Alice publishes a dataset (= publishes a datatoken)
    # For now, you're Alice:) Let's proceed.
    config = {
        'network': network,
        'privateKey': alice_private_key
    }
    ocean = Ocean.Ocean(config)
    token = ocean.createToken('localhost:8030')
    dt_address = token.getAddress()

    # 3. Alice mints 100 tokens
    token.mint(100)

    # 4. Alice transfers 1 token to Bob
    token.transfer(bob_address, 1)

    # 5. Bob consumes dataset
    # Now, you're Bob:)
    bob_config = {
        'network': network,
        'privateKey': bob_private_key,
    }
    bob_ocean = Ocean.Ocean(bob_config)
    token = bob_ocean.getToken(dt_address)
    _file = token.download()


if __name__ == '__main__':
    main()
