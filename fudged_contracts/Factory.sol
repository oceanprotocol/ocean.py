pragma solidity ^0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import './Deployer.sol';
import './IERC20Template.sol';
/**
* @title Factory contract
* @author Ocean Protocol Team
*
* @dev Implementation of Ocean DataTokens Factory
*
*      Factory deploys DataToken proxy contracts.
*      New DataToken proxy contracts are links to the template contract's bytecode. 
*      Proxy contract functionality is based on Ocean Protocol custom implementation of ERC1167 standard.
*/
contract Factory is Deployer {

    address payable private feeManager;
    address private tokenTemplate;
    mapping (string => address) private _tokenRegistry;
    
    event TokenCreated(
        address newTokenAddress, 
        address templateAddress,
        string tokenName
    );
    
    event TokenRegistered(
        address indexed tokenAddress,
        string indexed tokenName,
        string indexed tokenSymbol,
        uint256 tokenCap,
        address RegisteredBy,
        uint256 RegisteredAt,
        string blob
    );
    
    /**
     * @dev constructor
     *      Called on contract deployment. Could not be called with zero address parameters.
     * @param _template refers to the address of a deployed DataToken contract.
     * @param _feeManager refers to the address of a fee manager .
     */
    constructor(
        address _template,
        address payable _feeManager
    ) 
        public 
    {
        require(
            _template != address(0) && _feeManager != address(0),
            'Factory: Invalid TokenFactory initialization'
        );
        tokenTemplate = _template;
        feeManager = _feeManager;
    }

    /**
     * @dev Deploys new DataToken proxy contract.
     *      Template contract address could not be a zero address. 
     * @param _name refers to a new DataToken name.
     * @param _symbol refers to a new DataToken symbol.
     * @param _minter refers to an address that has minter rights.
     * @return address of a new proxy DataToken contract
     */
    function createToken(
        string memory _name, 
        string memory _symbol,
        uint256 _cap,
        string memory _blob,
        address _minter
    ) 
        public
        returns (address token)
    {
        require(
            _minter != address(0),
            'Factory: Invalid minter address'
        );

        require(
            _cap > 0,
            'Factory: Invalid cap value'
        );

        token = deploy(tokenTemplate);
        
        require(
            token != address(0),
            'Factory: Failed to perform minimal deploy of a new token'
        );

        IERC20Template tokenInstance = IERC20Template(token);
        tokenInstance.initialize(
            _name,
            _symbol,
            _minter,
            _cap,
            _blob,
            feeManager
        );

        require(
            tokenInstance.isInitialized(),
            'Factory: Unable to initialize token instance'
        );

	_tokenRegistry[_symbol] = token;
    
        emit TokenCreated(
            token, 
            tokenTemplate,
            _name
        );

        emit TokenRegistered(
            token,
            _name,
            _symbol,
            _cap,
            msg.sender,
            block.number,
            _blob
        );
    }
    // TODO: manage template list
    // TODO: Fee manager
    // TODO: Factory token double spend (hash based check)

    /**
     * @dev Returns address of a DataToken contract, given its symbol
     */
    function getTokenAddress(string memory _symbol) view public returns (address) {
        return _tokenRegistry[_symbol];
    }
    
}
