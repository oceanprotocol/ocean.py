#!/usr/bin/python3

from brownie import *

def main():
    Datatoken.deploy("Test Datatoken", "TST", 18, 1e21, {'from': accounts[0]})
