pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0


import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockOcean is ERC20("Ocean","Ocean"){


    constructor(address owner) {
        _mint(owner, 1e23);
    }

}