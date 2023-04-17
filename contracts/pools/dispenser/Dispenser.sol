pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "../../interfaces/IDispenser.sol";
import "../../interfaces/IERC20.sol";
import "../../interfaces/IERC20Template.sol";
import "../../interfaces/IERC721Template.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

import "../../utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Dispenser is ReentrancyGuard, IDispenser{
    using SafeMath for uint256;
    using SafeERC20 for IERC20;
    address public router;

    struct DataToken {
        bool active;  // if the dispenser is active for this datatoken
        address owner; // owner of this dispenser
        uint256 maxTokens; // max tokens to dispense
        uint256 maxBalance; // max balance of requester. 
        address allowedSwapper;
        //If the balance is higher, the dispense is rejected
    }
    mapping(address => DataToken) datatokens;
    address[] public datatokensList;
    
    
    event DispenserCreated(  // emited when a dispenser is created
        address indexed datatokenAddress,
        address indexed owner,
        uint256 maxTokens,
        uint256 maxBalance,
        address allowedSwapper
    );
    event DispenserActivated(  // emited when a dispenser is activated
        address indexed datatokenAddress
    );

    event DispenserDeactivated( // emited when a dispenser is deactivated
        address indexed datatokenAddress
    );
    event DispenserAllowedSwapperChanged( // emited when allowedSwapper is changed
        address indexed datatoken,
        address indexed newAllowedSwapper);
    
    event TokensDispensed( 
        // emited when tokens are dispended
        address indexed datatokenAddress,
        address indexed userAddress,
        uint256 amount
    );

    event OwnerWithdrawed(
        address indexed datatoken,
        address indexed owner,
        uint256 amount
    );

    modifier onlyRouter() {
        require(msg.sender == router, "Dispenser: only router");
        _;
    }

    modifier onlyOwner(address datatoken) {
        // allow only ERC20 Deployers or NFT Owner
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        IERC20Template dt = IERC20Template(datatoken);
        require(
            dt.isERC20Deployer(msg.sender) || 
            IERC721Template(dt.getERC721Address()).ownerOf(1) == msg.sender
            ,
            "Invalid owner"
        );
        _;
    }

    modifier onlyOwnerAndTemplate(address datatoken) {
        // allow only ERC20 Deployers or NFT Owner
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        IERC20Template dt = IERC20Template(datatoken);
        require(
            dt.isERC20Deployer(msg.sender) || 
            IERC721Template(dt.getERC721Address()).ownerOf(1) == msg.sender ||
            datatoken == msg.sender
            ,
            "Invalid owner"
        );
        _;
    }

    
    constructor(address _router) {
        require(_router != address(0), "Dispenser: Wrong Router address");
        router = _router;
    }

    /**
     * @dev getId
     *      Return template id in case we need different ABIs. 
     *      If you construct your own template, please make sure to change the hardcoded value
     */
    function getId() pure public returns (uint8) {
        return 1;
    }
    /**
     * @dev status
     *      Get information about a datatoken dispenser
     * @param datatoken refers to datatoken address.
     * @return active - if the dispenser is active for this datatoken
     * @return owner - owner of this dispenser
     * @return isMinter  - check the datatoken contract if the dispenser has mint roles
     * @return maxTokens - max tokens to dispense
     * @return maxBalance - max balance of requester. If the balance is higher, the dispense is rejected
     * @return balance - internal balance of the contract (if any)
     * @return allowedSwapper - address allowed to request DT if != 0
     */
    function status(address datatoken) 
    external view 
    returns(bool active,address owner,
    bool isMinter,uint256 maxTokens,uint256 maxBalance, uint256 balance, address allowedSwapper){
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        active = datatokens[datatoken].active;
        owner = datatokens[datatoken].owner;
        maxTokens = datatokens[datatoken].maxTokens;
        maxBalance = datatokens[datatoken].maxBalance;
        IERC20Template tokenInstance = IERC20Template(datatoken);
        balance = tokenInstance.balanceOf(address(this));
        isMinter = tokenInstance.isMinter(address(this));
        allowedSwapper = datatokens[datatoken].allowedSwapper;
    }

    /**
     * @dev create
     *      Create a new dispenser
     * @param datatoken refers to datatoken address.
     * @param maxTokens - max tokens to dispense
     * @param maxBalance - max balance of requester.
     * @param owner - owner
     * @param allowedSwapper - if !=0, only this address can request DTs
     */
    function create(address datatoken,uint256 maxTokens, uint256 maxBalance, address owner, address allowedSwapper)
        external onlyRouter{
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        require(
            datatokens[datatoken].owner == address(0) || datatokens[datatoken].owner == owner,
            'Datatoken already created'
        );
        datatokens[datatoken].active = true;
        datatokens[datatoken].owner = owner;
        datatokens[datatoken].maxTokens = maxTokens;
        datatokens[datatoken].maxBalance = maxBalance;
        datatokens[datatoken].allowedSwapper = allowedSwapper;
        datatokensList.push(datatoken);
        emit DispenserCreated(datatoken, owner, maxTokens, maxBalance, allowedSwapper);
        emit DispenserAllowedSwapperChanged(datatoken, allowedSwapper);
    }
    /**
     * @dev activate
     *      Activate a new dispenser
     * @param datatoken refers to datatoken address.
     * @param maxTokens - max tokens to dispense
     * @param maxBalance - max balance of requester.
     */
    function activate(address datatoken,uint256 maxTokens, uint256 maxBalance)
        external onlyOwner(datatoken){
        datatokens[datatoken].active = true;
        datatokens[datatoken].maxTokens = maxTokens;
        datatokens[datatoken].maxBalance = maxBalance;
        datatokensList.push(datatoken);
        emit DispenserActivated(datatoken);
    }

    /**
     * @dev deactivate
     *      Deactivate an existing dispenser
     * @param datatoken refers to datatoken address.
     */
    function deactivate(address datatoken) external onlyOwner(datatoken){
        datatokens[datatoken].active = false;
        emit DispenserDeactivated(datatoken);
    }

    /**
     * @dev setAllowedSwapper
     *      Sets a new allowedSwapper
     * @param datatoken refers to datatoken address.
     * @param newAllowedSwapper refers to the new allowedSwapper
     */
    function setAllowedSwapper(address datatoken, address newAllowedSwapper) external onlyOwner(datatoken){
        datatokens[datatoken].allowedSwapper= newAllowedSwapper;
        emit DispenserAllowedSwapperChanged(datatoken, newAllowedSwapper);
    }

    

    /**
     * @dev dispense
     *  Dispense datatokens to caller. 
     *  The dispenser must be active, hold enough DT (or be able to mint more) 
     *  and respect maxTokens/maxBalance requirements
     * @param datatoken refers to datatoken address.
     * @param amount amount of datatokens required.
     * @param destination refers to who will receive the tokens
     */
    function dispense(address datatoken, uint256 amount, address destination) external nonReentrant payable{
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        require(
            datatokens[datatoken].active,
            'Dispenser not active'
        );
        require(
            amount > 0,
            'Invalid zero amount'
        );
        require(
            datatokens[datatoken].maxTokens >= amount,
            'Amount too high'
        );
        if(datatokens[datatoken].allowedSwapper != address(0)){
            require(
                datatokens[datatoken].allowedSwapper == msg.sender,
                "This address is not allowed to request DT"
            );
        }
        
        IERC20Template tokenInstance = IERC20Template(datatoken);
        uint256 callerBalance = tokenInstance.balanceOf(destination);
        require(
            callerBalance<datatokens[datatoken].maxBalance,
            'Caller balance too high'
        );
        uint256 ourBalance = tokenInstance.balanceOf(address(this));
        if(ourBalance<amount && tokenInstance.isMinter(address(this))){ 
            //we need to mint the difference if we can
            tokenInstance.mint(address(this),amount - ourBalance);
            ourBalance = tokenInstance.balanceOf(address(this));
        }
        require(
            ourBalance>=amount,
            'Not enough reserves'
        );
        emit TokensDispensed(datatoken, destination, amount);
        IERC20(datatoken).safeTransfer(destination,amount);
    }

    /**
     * @dev ownerWithdraw
     *      Withdraw all datatokens in this dispenser balance to ERC20.getPaymentCollector()
     * @param datatoken refers to datatoken address.
     */
    function ownerWithdraw(address datatoken) external onlyOwnerAndTemplate(datatoken) nonReentrant {
        require(
            datatoken != address(0),
            'Invalid token contract address'
        );
        _ownerWithdraw(datatoken);
    }

    function _ownerWithdraw(address datatoken) internal{
        IERC20Template tokenInstance = IERC20Template(datatoken);
        address destination = tokenInstance.getPaymentCollector();
        uint256 ourBalance = tokenInstance.balanceOf(address(this));
        if(ourBalance>0){
            emit OwnerWithdrawed(datatoken, destination, ourBalance);
            IERC20(datatoken).safeTransfer(destination,ourBalance);
        }
    }
}