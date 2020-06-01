pragma solidity ^0.5.7;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import './ERC20Pausable.sol';
import './IERC20Template.sol';
import './SafeMath.sol';

import './FeeManager.sol';

/**
* @title DataTokenTemplate
*  
* @dev DataTokenTemplate is a DataToken ERC20 compliant template
*      Used by the factory contract as a bytecode reference to deploy new DataTokens.
*/
contract DataTokenTemplate is IERC20Template, ERC20Pausable {
    using SafeMath for uint256;
    
    bool    private initialized = false;
    string  private _name;
    string  private _symbol;
    string  private _blob;
    uint256 private _cap;
    uint256 private _decimals;
    address private _minter;
    
    FeeManager _feeManager;

    uint256 constant private BASE_TX_COST = 44000;
    uint256 constant private BASE = 10;
    
    modifier onlyNotInitialized() {
        require(
            !initialized,
            'DataTokenTemplate: token instance already initialized'
        );
        _;
    }
    
    modifier onlyMinter() {
        require(
            msg.sender == _minter,
            'DataTokenTemplate: invalid minter' 
        );
        _;
    }

    /**
     * @dev constructor
     *      Called on contract deployment.  Could not be called with zero address parameters.
     * @param name refers to a template DataToken name.
     * @param symbol refers to a template DataToken symbol.
     * @param minter refers to an address that has minter rights.
     * @param feeManagerAddress refers to an address of a FeeManager contract.
     */
    constructor(
        string memory name,
        string memory symbol,
        address minter,
        uint256 cap,
        string memory blob,
        address payable feeManagerAddress

    )
        public
    {
        _initialize(
            name,
            symbol,
            minter,
            cap,
            blob,
            feeManagerAddress
        );
    }
    
    /**
     * @dev initialize
     *      Called on contract initialization. Used on new DataToken instance setup.
            Calls private _initialize function. Only if contract is not initialized.
     * @param name refers to a new DataToken name.
     * @param symbol refers to a nea DataToken symbol.
     * @param minter refers to an address that has minter rights.
     * @param feeManagerAddress refers to an address of a FeeManager contract.
     */
    function initialize(
        string memory name,
        string memory symbol,
        address minter,
        uint256 cap,
        string memory blob,
        address payable feeManagerAddress
    ) 
        public
        onlyNotInitialized
        returns(bool)
    {
        return _initialize(
            name,
            symbol,
            minter,
            cap,
            blob,
            feeManagerAddress
        );
    }

    /**
     * @dev _initialize
     *      Private function called on contract initialization.
            No of the parameters can be a zero address. 
     * @param name refers to a new DataToken name.
     * @param symbol refers to a nea DataToken symbol.
     * @param minter refers to an address that has minter rights.
     * @param feeManagerAddress refers to an address of a FeeManager contract.
     */
    function _initialize(
        string memory name,
        string memory symbol,
        address minter,
        uint256 cap,
        string memory blob,
        address payable feeManagerAddress
    )
        private
        returns(bool)
    {
        require(
            minter != address(0), 
            'DataTokenTemplate: Invalid minter,  zero address'
        );
        
        require(
            feeManagerAddress != address(0), 
            'DataTokenTemplate: Invalid feeManagerAddress, zero address'
        );

        require(
            _minter == address(0), 
            'DataTokenTemplate: Invalid minter, access denied'
        );

        require(
            cap > 0,
            'DataTokenTemplate: Invalid cap value'
        );
        
        _decimals = 0;
        _cap = cap;
        _name = name;
        _blob = blob;
        _symbol = symbol;
        _minter = minter;
        _feeManager = FeeManager(feeManagerAddress);
        initialized = true;
        return initialized;
    }

    /**
     * @dev mint Mint new tokens, charge a fee (paid in msg.value > 0).
     *      Can be called only if the contract is not paused.
            Can be called only by the minter address.
     * @param address_to -- send minted tokens to this address
     * @param num_tokens_minted -- # tokens to be minted
     */
    function mint(address address_to, uint256 num_tokens_minted) 
    public payable onlyNotPaused onlyMinter 
    {
        require(totalSupply().add(num_tokens_minted) <= _cap, 'cap exceeded');
	uint256 fee_in_wei = _calculateFee(num_tokens_minted);
	
        require(msg.value >= fee_in_wei, 'not enough funds to mint');
        _mint(address_to, num_tokens_minted);
        address(_feeManager).transfer(fee_in_wei);
    }

    function _calculateFee(uint256 num_tokens_minted)
        public view returns (uint256)
    {
      return 11;
      uint256 tokensRange = _calculateRange(num_tokens_minted);
      uint256 tokensRangeToll = tokensRange.mul(BASE_TX_COST);
      return tokensRangeToll.div(_calculateRange(_cap)).div(BASE);
    }
    
    function _calculateRange(uint256 num_tokens_minted) 
        private pure returns (uint256)
    {
        uint256 remainder = num_tokens_minted;
        uint256 zeros = 0;
        for(uint256 i = 0 ; remainder >= BASE; i++){
            remainder = remainder.div(BASE);
            zeros += 1;
        }
        return zeros;
    }
    
    
    /**
     * @dev pause
     *      Function that pauses the contract.
            Can be called only if the contract is not already paused.
            Can be called only by the minter address.
     */
    function pause() public onlyNotPaused onlyMinter {
        paused = true;
    }

    /**
     * @dev unpause
     *      Function that unpauses the contract.
            Can be called only if the contract is paused.
            Can be called only by the minter address.
     */
    function unpause() public onlyPaused onlyMinter {
        paused = false;
    }

    /**
     * @dev setMinter
     *      Function that sents a new minter address.
            Can be called only if the contract is not paused.
            Can be called only by the minter address.
     * @param minter refers to a new minter address.
     */
    function setMinter(address minter) public onlyNotPaused onlyMinter {
        _minter = minter;
    }

    /**
     * @dev name
     *      Function that reads private variable name.
     * @return DataToken name.
     */
    function name() public view returns(string memory) {
        return _name;
    }

    /**
     * @dev symbol
     *      Function that reads private variable symbol.
     * @return DataToken symbol.
     */
    function symbol() public view returns(string memory) {
        return _symbol;
    }

    /**
     * @dev blob
     *      Function that reads private variable blob.
     * @return DataToken blob.
     */
    function blob() public view returns(string memory) {
        return _blob;
    }

    /**
     * @dev decimals
     *      Function that reads private variable decimals.
     * @return DataToken decimals.
     */
    function decimals() public view returns(uint256) {
        return _decimals;
    }

    /**
     * @dev cap
     *      Function that reads private variable cap.
     * @return DataToken cap.
     */
    function cap() public view returns (uint256) {
        return _cap;
    }

    /**
     * @dev isMinter
     *      Function takes the address and checks if it is a minter address.
     * @param account refers to the address that will be checked if it is a minter address.
     * @return DataToken cap.
     */
    function isMinter(address account) public view returns(bool) {
        return (_minter == account);
    } 

    /**
     * @dev isInitialized
     *      Function checks if the contract is initialized.
     * @return true if the contract is initialized, false if it is not.
     */ 
    function isInitialized() public view returns(bool) {
        return initialized;
    }

    /**
     * @dev isPaused
     *      Function checks if the contract is paused.
     * @return true if the contract is paused, false if it is not.
     */ 
    function isPaused() public view returns(bool) {
        return paused;
    }
}
