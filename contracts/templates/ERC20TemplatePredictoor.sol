pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0

import "../interfaces/IERC721Template.sol";
import "../interfaces/IERC20Template.sol";
import "../interfaces/IFactoryRouter.sol";
import "../interfaces/IFixedRateExchange.sol";
import "../interfaces/IDispenser.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "../utils/ERC20Roles.sol";

/**
 * @title DatatokenTemplate
 *
 * @dev ERC20TemplateEnterprise is an ERC20 compliant token template
 *      Used by the factory contract as a bytecode reference to
 *      deploy new Datatokens.
 * IMPORTANT CHANGES:
 *  - buyFromFreAndOrder function:  one call to buy a DT from the minting capable FRE, startOrder and burn the DT
 *  - buyFromDispenserAndOrder function:  one call to fetch a DT from the Dispenser, startOrder and burn the DT
 *  - creation of pools is not allowed
 */
contract ERC20TemplatePredictoor is
    ERC20("test", "testSymbol"),
    ERC20Roles,
    ERC20Burnable,
    ReentrancyGuard
{
    using SafeMath for uint256;
    using SafeERC20 for IERC20;
    string private _name;
    string private _symbol;
    uint256 private _cap;
    uint8 private constant _decimals = 18;
    bool private initialized = false;
    address private _erc721Address;
    address private paymentCollector;
    address private publishMarketFeeAddress;
    address private publishMarketFeeToken;
    uint256 private publishMarketFeeAmount;

    uint256 public constant BASE = 1e18;

    // -------------------------- PREDICTOOR --------------------------
    struct Prediction {
        bool predval;
        uint256 stake;
        address predictoor;
        bool paid;
    }
    struct Subscription {
        address user;
        uint256 expires;
    }
    mapping(uint256 => mapping(address => Prediction)) predobjs; // id to prediction object
    mapping(uint256 => uint256) predcounter; // block num to id counter
    mapping(uint256 => uint256) agg_predvals_numer;
    mapping(uint256 => uint256) agg_predvals_denom;
    mapping(uint256 => bool) truevals;
    mapping(uint256 => bool) truval_submitted;
    mapping(uint256 => uint256) subscription_revenue_at_block; //income registred
    mapping(address => Subscription) subscriptions; // valid subscription per user
    uint256 blocks_per_epoch;
    uint256 blocks_per_subscription;
    uint256 truval_submit_timeout_block = 3;
    address stake_token;
    bool paused = false;
    // -------------------------- PREDICTOOR --------------------------

    // EIP 2612 SUPPORT
    bytes32 public DOMAIN_SEPARATOR;
    // keccak256("Permit(address owner,address spender,uint256 value,uint256 nonce,uint256 deadline)");
    bytes32 public constant PERMIT_TYPEHASH =
        0x6e71edae12b1b97f4d1f60370fef10105fa2faae0126114a169c64845d6126c9;

    mapping(address => uint256) public nonces;
    address public router;

    struct fixedRate {
        address contractAddress;
        bytes32 id;
    }
    fixedRate[] fixedRateExchanges;
    address[] dispensers;

    struct providerFee {
        address providerFeeAddress;
        address providerFeeToken; // address of the token
        uint256 providerFeeAmount; // amount to be transfered to provider
        uint8 v; // v of provider signed message
        bytes32 r; // r of provider signed message
        bytes32 s; // s of provider signed message
        uint256 validUntil; //validity expresses in unix timestamp
        bytes providerData; //data encoded by provider
    }

    struct consumeMarketFee {
        address consumeMarketFeeAddress;
        address consumeMarketFeeToken; // address of the token marketplace wants to add fee on top
        uint256 consumeMarketFeeAmount; // amount to be transfered to marketFeeCollector
    }

    event OrderStarted(
        address indexed consumer,
        address payer,
        uint256 amount,
        uint256 serviceIndex,
        uint256 timestamp,
        address indexed publishMarketAddress,
        uint256 blockNumber
    );

    event OrderReused(
        bytes32 orderTxId,
        address caller,
        uint256 timestamp,
        uint256 number
    );

    event OrderExecuted(
        address indexed providerAddress,
        address indexed consumerAddress,
        bytes32 orderTxId,
        bytes providerData,
        bytes providerSignature,
        bytes consumerData,
        bytes consumerSignature,
        uint256 timestamp,
        uint256 blockNumber
    );

    // emited for every order
    event PublishMarketFee(
        address indexed PublishMarketFeeAddress,
        address indexed PublishMarketFeeToken,
        uint256 PublishMarketFeeAmount
    );

    // emited for every order
    event ConsumeMarketFee(
        address indexed consumeMarketFeeAddress,
        address indexed consumeMarketFeeToken,
        uint256 consumeMarketFeeAmount
    );

    event PublishMarketFeeChanged(
        address caller,
        address PublishMarketFeeAddress,
        address PublishMarketFeeToken,
        uint256 PublishMarketFeeAmount
    );

    event MinterProposed(address currentMinter, address newMinter);

    event MinterApproved(address currentMinter, address newMinter);

    event NewFixedRate(
        bytes32 exchangeId,
        address indexed owner,
        address exchangeContract,
        address indexed baseToken
    );
    event NewDispenser(address dispenserContract);

    event NewPaymentCollector(
        address indexed caller,
        address indexed _newPaymentCollector,
        uint256 timestamp,
        uint256 blockNumber
    );

    modifier onlyNotInitialized() {
        require(
            !initialized,
            "ERC20Template: token instance already initialized"
        );
        _;
    }
    modifier onlyNFTOwner() {
        require(
            msg.sender == IERC721Template(_erc721Address).ownerOf(1),
            "ERC20Template: not NFTOwner"
        );
        _;
    }

    modifier onlyPublishingMarketFeeAddress() {
        require(
            msg.sender == publishMarketFeeAddress,
            "ERC20Template: not publishMarketFeeAddress"
        );
        _;
    }

    modifier onlyERC20Deployer() {
        require(
            IERC721Template(_erc721Address)
                .getPermissions(msg.sender)
                .deployERC20 ||
                IERC721Template(_erc721Address).ownerOf(1) == msg.sender,
            "ERC20Template: NOT DEPLOYER ROLE"
        );
        _;
    }

    modifier blocknumOnSlot(uint256 num) {
        require(
            blocknum_is_on_a_slot(num),
            "Predictoor: blocknum must be on a slot"
        );
        _;
    }

    /**
     * @dev initialize
     *      Called prior contract initialization (e.g creating new Datatoken instance)
     *      Calls private _initialize function. Only if contract is not initialized.
     * @param strings_ refers to an array of strings
     *                      [0] = name token
     *                      [1] = symbol
     * @param addresses_ refers to an array of addresses passed by user
     *                     [0]  = minter account who can mint datatokens (can have multiple minters)
     *                     [1]  = paymentCollector initial paymentCollector for this DT
     *                     [2]  = publishing Market Address
     *                     [3]  = publishing Market Fee Token
     *                     [4]  = predictoor stake token
     * @param factoryAddresses_ refers to an array of addresses passed by the factory
     *                     [0]  = erc721Address
     *                     [1]  = router address
     *
     * @param uints_  refers to an array of uints
     *                     [0] = cap_ the total ERC20 cap
     *                     [1] = publishing Market Fee Amount
     *                     [2] = s_per_block,
     *                     [3] = s_per_epoch,
     *                     [4] = s_per_subscription,
     * @param bytes_  refers to an array of bytes
     *                     Currently not used, usefull for future templates
     */
    function initialize(
        string[] calldata strings_,
        address[] calldata addresses_,
        address[] calldata factoryAddresses_,
        uint256[] calldata uints_,
        bytes[] calldata bytes_
    ) external onlyNotInitialized returns (bool) {
        return
            _initialize(
                strings_,
                addresses_,
                factoryAddresses_,
                uints_,
                bytes_
            );
    }

    /**
     * @dev _initialize
     *      Private function called on contract initialization.
     * @param strings_ refers to an array of strings
     *                      [0] = name token
     *                      [1] = symbol
     * @param addresses_ refers to an array of addresses passed by user
     *                     [0]  = minter account who can mint datatokens (can have multiple minters)
     *                     [1]  = paymentCollector initial paymentCollector for this DT
     *                     [2]  = publishing Market Address
     *                     [3]  = publishing Market Fee Token
     *                     [4]  = predictoor stake token
     * @param factoryAddresses_ refers to an array of addresses passed by the factory
     *                     [0]  = erc721Address
     *                     [1]  = router address
     *
     * @param uints_  refers to an array of uints
     *                     [0] = cap_ the total ERC20 cap
     *                     [1] = publishing Market Fee
     *                     [2] = s_per_block,
     *                     [3] = s_per_epoch,
     *                     [4] = s_per_subscription,
     * param bytes_  refers to an array of bytes
     *                     Currently not used, usefull for future templates
     */
    function _initialize(
        string[] memory strings_,
        address[] memory addresses_,
        address[] memory factoryAddresses_,
        uint256[] memory uints_,
        bytes[] memory
    ) private returns (bool) {
        address erc721Address = factoryAddresses_[0];
        router = factoryAddresses_[1];
        require(
            erc721Address != address(0),
            "ERC20Template: Invalid minter,  zero address"
        );

        require(
            router != address(0),
            "ERC20Template: Invalid router, zero address"
        );

        require(uints_[0] != 0, "DatatokenTemplate: Invalid cap value");
        _cap = uints_[0];
        _name = strings_[0];
        _symbol = strings_[1];
        _erc721Address = erc721Address;

        initialized = true;
        // add a default minter, similar to what happens with manager in the 721 contract
        _addMinter(addresses_[0]);
        // set payment collector to this contract, so we can get the $$$
        _setPaymentCollector(address(this));
        emit NewPaymentCollector(
            msg.sender,
            addresses_[1],
            block.timestamp,
            block.number
        );

        publishMarketFeeAddress = addresses_[2];
        publishMarketFeeToken = addresses_[3];
        publishMarketFeeAmount = uints_[1];
        emit PublishMarketFeeChanged(
            msg.sender,
            publishMarketFeeAddress,
            publishMarketFeeToken,
            publishMarketFeeAmount
        );
        uint256 chainId;
        assembly {
            chainId := chainid()
        }
        DOMAIN_SEPARATOR = keccak256(
            abi.encode(
                keccak256(
                    "EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
                ),
                keccak256(bytes(_name)),
                keccak256(bytes("1")), // version, could be any other value
                chainId,
                address(this)
            )
        );

        stake_token = addresses_[4];
        _update_seconds(uints_[2], uints_[3], uints_[4], uints_[5]);
        return initialized;
    }

    /**
     * @dev createFixedRate
     *      Creates a new FixedRateExchange setup.
     * @param fixedPriceAddress fixedPriceAddress
     * @param addresses array of addresses [baseToken,owner,marketFeeCollector]
     * @param uints array of uints [baseTokenDecimals,datatokenDecimals, fixedRate, marketFee, withMint]
     * @return exchangeId
     */
    function createFixedRate(
        address fixedPriceAddress,
        address[] memory addresses,
        uint256[] memory uints
    ) external onlyERC20Deployer nonReentrant returns (bytes32 exchangeId) {
        require(
            stake_token == addresses[0],
            "Cannot create FRE with baseToken!=stake_token"
        );
        //force FRE allowedSwapper to this contract address. no one else can swap because we need to record the income
        addresses[3] = address(this);
        if (uints[4] > 0) _addMinter(fixedPriceAddress);
        exchangeId = IFactoryRouter(router).deployFixedRate(
            fixedPriceAddress,
            addresses,
            uints
        );
        emit NewFixedRate(
            exchangeId,
            addresses[1],
            fixedPriceAddress,
            addresses[0]
        );
        fixedRateExchanges.push(fixedRate(fixedPriceAddress, exchangeId));
    }

    /**
     * @dev createDispenser
     *      Creates a new Dispenser
     * @param _dispenser dispenser contract address
     * @param maxTokens - max tokens to dispense
     * @param maxBalance - max balance of requester.
     * @param withMint - with MinterRole
     * @param allowedSwapper allowed swappers
     */
    function createDispenser(
        address _dispenser,
        uint256 maxTokens,
        uint256 maxBalance,
        bool withMint,
        address allowedSwapper
    ) external onlyERC20Deployer nonReentrant {
        // add dispenser contract as minter if withMint == true
        if (withMint) _addMinter(_dispenser);
        dispensers.push(_dispenser);
        emit NewDispenser(_dispenser);
        IFactoryRouter(router).deployDispenser(
            _dispenser,
            address(this),
            maxTokens,
            maxBalance,
            msg.sender,
            allowedSwapper
        );
    }

    /**
     * @dev mint
     *      Only the minter address can call it.
     *      msg.value should be higher than zero and gt or eq minting fee
     * @param account refers to an address that token is going to be minted to.
     * @param value refers to amount of tokens that is going to be minted.
     */
    function mint(address account, uint256 value) external {
        require(permissions[msg.sender].minter, "ERC20Template: NOT MINTER");
        require(
            totalSupply().add(value) <= _cap,
            "DatatokenTemplate: cap exceeded"
        );
        _mint(account, value);
    }

    /**
     * @dev startOrder
     *      called by payer or consumer prior ordering a service consume on a marketplace.
     *      Requires previous approval of consumeFeeToken and publishMarketFeeToken
     * @param consumer is the consumer address (payer could be different address)
     * @param serviceIndex service index in the metadata
     * @param _providerFee provider fee
     * @param _consumeMarketFee consume market fee
     */
    function startOrder(
        address consumer,
        uint256 serviceIndex,
        providerFee calldata _providerFee,
        consumeMarketFee calldata _consumeMarketFee
    ) public {
        uint256 amount = 1e18; // we always pay 1 DT. No more, no less
        require(
            balanceOf(msg.sender) >= amount,
            "Not enough datatokens to start Order"
        );
        emit OrderStarted(
            consumer,
            msg.sender,
            amount,
            serviceIndex,
            block.timestamp,
            publishMarketFeeAddress,
            block.number
        );
        // publishMarketFee
        // Requires approval for the publishMarketFeeToken of publishMarketFeeAmount
        // skip fee if amount == 0 or feeToken == 0x0 address or feeAddress == 0x0 address
        if (
            publishMarketFeeAmount > 0 &&
            publishMarketFeeToken != address(0) &&
            publishMarketFeeAddress != address(0)
        ) {
            _pullUnderlying(
                publishMarketFeeToken,
                msg.sender,
                publishMarketFeeAddress,
                publishMarketFeeAmount
            );
            emit PublishMarketFee(
                publishMarketFeeAddress,
                publishMarketFeeToken,
                publishMarketFeeAmount
            );
        }

        // consumeMarketFee
        // Requires approval for the FeeToken
        // skip fee if amount == 0 or feeToken == 0x0 address or feeAddress == 0x0 address
        if (
            _consumeMarketFee.consumeMarketFeeAmount > 0 &&
            _consumeMarketFee.consumeMarketFeeToken != address(0) &&
            _consumeMarketFee.consumeMarketFeeAddress != address(0)
        ) {
            _pullUnderlying(
                _consumeMarketFee.consumeMarketFeeToken,
                msg.sender,
                _consumeMarketFee.consumeMarketFeeAddress,
                _consumeMarketFee.consumeMarketFeeAmount
            );
            emit ConsumeMarketFee(
                _consumeMarketFee.consumeMarketFeeAddress,
                _consumeMarketFee.consumeMarketFeeToken,
                _consumeMarketFee.consumeMarketFeeAmount
            );
        }
        Subscription memory sub = Subscription(
            consumer,
            block.number + blocks_per_subscription
        );
        subscriptions[consumer] = sub;

        burn(amount);
    }

    /**
     * @dev addMinter
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple minters
     * @param _minter new minter address
     */

    function addMinter(address _minter) external onlyERC20Deployer {
        _addMinter(_minter);
    }

    /**
     * @dev removeMinter
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple minters
     * @param _minter minter address to remove
     */

    function removeMinter(address _minter) external onlyERC20Deployer {
        _removeMinter(_minter);
    }

    /**
     * @dev addPaymentManager (can set who's going to collect fee when consuming orders)
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple paymentCollectors
     * @param _paymentManager new minter address
     */

    function addPaymentManager(
        address _paymentManager
    ) external onlyERC20Deployer {
        _addPaymentManager(_paymentManager);
    }

    /**
     * @dev removePaymentManager
     *      Only ERC20Deployer (at 721 level) can update.
     *      There can be multiple paymentManagers
     * @param _paymentManager _paymentManager address to remove
     */

    function removePaymentManager(
        address _paymentManager
    ) external onlyERC20Deployer {
        _removePaymentManager(_paymentManager);
    }

    /**
     * @dev setData
     *      Only ERC20Deployer (at 721 level) can call it.
     *      This function allows to store data with a preset key (keccak256(ERC20Address)) into NFT 725 Store
     * @param _value data to be set with this key
     */

    function setData(bytes calldata _value) external onlyERC20Deployer {
        bytes32 key = keccak256(abi.encodePacked(address(this)));
        IERC721Template(_erc721Address).setDataERC20(key, _value);
    }

    /**
     * @dev cleanPermissions()
     *      Only NFT Owner (at 721 level) can call it.
     *      This function allows to remove all minters, feeManagers and reset the paymentCollector
     *
     */

    function cleanPermissions() external onlyNFTOwner {
        _internalCleanPermissions();
    }

    /**
     * @dev cleanFrom721()
     *      OnlyNFT(721) Contract can call it.
     *      This function allows to remove all minters, feeManagers and reset the paymentCollector
     *       This function is used when transferring an NFT to a new owner,
     * so that permissions at ERC20level (minter,feeManager,paymentCollector) can be reset.
     *
     */
    function cleanFrom721() external {
        require(
            msg.sender == _erc721Address,
            "ERC20Template: NOT 721 Contract"
        );
        _internalCleanPermissions();
    }

    function _internalCleanPermissions() internal {
        uint256 totalLen = fixedRateExchanges.length + dispensers.length;
        uint256 curentLen = 0;
        address[] memory previousMinters = new address[](totalLen);
        // loop though fixedrates, empty and preserve the minter rols if exists
        uint256 i;
        for (i = 0; i < fixedRateExchanges.length; i++) {
            IFixedRateExchange fre = IFixedRateExchange(
                fixedRateExchanges[i].contractAddress
            );
            (
                ,
                ,
                ,
                ,
                ,
                ,
                ,
                ,
                ,
                uint256 dtBalance,
                uint256 btBalance,
                bool withMint
            ) = fre.getExchange(fixedRateExchanges[i].id);
            if (btBalance > 0)
                fre.collectBT(fixedRateExchanges[i].id, btBalance);
            if (dtBalance > 0)
                fre.collectDT(fixedRateExchanges[i].id, dtBalance);
            // add it to the list of minters
            if (
                isMinter(fixedRateExchanges[i].contractAddress) &&
                withMint == true
            ) {
                previousMinters[curentLen] = fixedRateExchanges[i]
                    .contractAddress;
                curentLen++;
            }
        }
        // loop though dispenser and preserve the minter rols if exists
        for (i = 0; i < dispensers.length; i++) {
            IDispenser(dispensers[i]).ownerWithdraw(address(this));
            if (isMinter(dispensers[i])) {
                previousMinters[curentLen] = dispensers[i];
                curentLen++;
            }
        }
        // clear all permisions
        _cleanPermissions();
        // set collector to 0
        paymentCollector = address(0);
        // add existing minter roles for fixedrate & dispensers
        for (i = 0; i < curentLen; i++) {
            _addMinter(previousMinters[i]);
        }
    }

    /**
     * @dev setPaymentCollector
     *      Only feeManager can call it
     *      This function allows to set a newPaymentCollector (receives DT when consuming)
            If not set the paymentCollector is the NFT Owner
     * @param _newPaymentCollector new fee collector 
     */

    function setPaymentCollector(address _newPaymentCollector) external {
        // does nothing for this template, paymentCollector is always address(this)
    }

    /**
     * @dev _setPaymentCollector
     * @param _newPaymentCollector new fee collector
     */

    function _setPaymentCollector(address _newPaymentCollector) internal {
        paymentCollector = _newPaymentCollector;
    }

    /**
     * @dev getPublishingMarketFee
     *      Get publishingMarket Fee
     *      This function allows to get the current fee set by the publishing market
     */
    function getPublishingMarketFee()
        external
        view
        returns (address, address, uint256)
    {
        return (
            publishMarketFeeAddress,
            publishMarketFeeToken,
            publishMarketFeeAmount
        );
    }

    /**
     * @dev setPublishingMarketFee
     *      Only publishMarketFeeAddress can call it
     *      This function allows to set the fee required by the publisherMarket
     * @param _publishMarketFeeAddress  new _publishMarketFeeAddress
     * @param _publishMarketFeeToken new _publishMarketFeeToken
     * @param _publishMarketFeeAmount new fee amount
     */
    function setPublishingMarketFee(
        address _publishMarketFeeAddress,
        address _publishMarketFeeToken,
        uint256 _publishMarketFeeAmount
    ) external onlyPublishingMarketFeeAddress {
        require(
            _publishMarketFeeAddress != address(0),
            "Invalid _publishMarketFeeAddress address"
        );
        require(
            _publishMarketFeeToken != address(0),
            "Invalid _publishMarketFeeToken address"
        );
        publishMarketFeeAddress = _publishMarketFeeAddress;
        publishMarketFeeToken = _publishMarketFeeToken;
        publishMarketFeeAmount = _publishMarketFeeAmount;
        emit PublishMarketFeeChanged(
            msg.sender,
            _publishMarketFeeAddress,
            _publishMarketFeeToken,
            _publishMarketFeeAmount
        );
    }

    /**
     * @dev getId
     *      Return template id in case we need different ABIs.
     *      If you construct your own template, please make sure to change the hardcoded value
     */
    function getId() public pure returns (uint8) {
        return 3;
    }

    /**
     * @dev name
     *      It returns the token name.
     * @return Datatoken name.
     */
    function name() public view override returns (string memory) {
        return _name;
    }

    /**
     * @dev symbol
     *      It returns the token symbol.
     * @return Datatoken symbol.
     */
    function symbol() public view override returns (string memory) {
        return _symbol;
    }

    /**
     * @dev getERC721Address
     *      It returns the parent ERC721
     * @return ERC721 address.
     */
    function getERC721Address() public view returns (address) {
        return _erc721Address;
    }

    /**
     * @dev decimals
     *      It returns the token decimals.
     *      how many supported decimal points
     * @return Datatoken decimals.
     */
    function decimals() public pure override returns (uint8) {
        return _decimals;
    }

    /**
     * @dev cap
     *      it returns the capital.
     * @return Datatoken cap.
     */
    function cap() external view returns (uint256) {
        return _cap;
    }

    /**
     * @dev isInitialized
     *      It checks whether the contract is initialized.
     * @return true if the contract is initialized.
     */

    function isInitialized() external view returns (bool) {
        return initialized;
    }

    /**
     * @dev getPaymentCollector
     *      It returns the current paymentCollector
     * @return paymentCollector address
     */

    function getPaymentCollector() public view returns (address) {
        return address(this);
    }

    /**
     * @dev fallback function
     *      this is a default fallback function in which receives
     *      the collected ether.
     */
    fallback() external payable {}

    /**
     * @dev receive function
     *      this is a default receive function in which receives
     *      the collected ether.
     */
    receive() external payable {}

    /**
     * @dev withdrawETH
     *      transfers all the accumlated ether the collector account
     */
    function withdrawETH() external payable {
        payable(getPaymentCollector()).transfer(address(this).balance);
    }

    struct OrderParams {
        address consumer;
        uint256 serviceIndex;
        providerFee _providerFee;
        consumeMarketFee _consumeMarketFee;
    }
    struct FreParams {
        address exchangeContract;
        bytes32 exchangeId;
        uint256 maxBaseTokenAmount;
        uint256 swapMarketFee;
        address marketFeeAddress;
    }

    /**
     * @dev buyFromFre
     *      Buys 1 DT from the FRE
     */
    function buyFromFre(FreParams calldata _freParams) internal {
        // get exchange info
        IFixedRateExchange fre = IFixedRateExchange(
            _freParams.exchangeContract
        );
        (, address datatoken, , address baseToken, , , , , , , , ) = fre
            .getExchange(_freParams.exchangeId);
        require(
            datatoken == address(this),
            "This FixedRate is not providing this DT"
        );
        // get token amounts needed
        (uint256 baseTokenAmount, , , ) = fre.calcBaseInGivenOutDT(
            _freParams.exchangeId,
            1e18, // we always take 1 DT
            _freParams.swapMarketFee
        );
        require(
            baseTokenAmount <= _freParams.maxBaseTokenAmount,
            "FixedRateExchange: Too many base tokens"
        );

        //transfer baseToken to us first
        _pullUnderlying(baseToken, msg.sender, address(this), baseTokenAmount);
        //approve FRE to spend baseTokens
        IERC20(baseToken).safeIncreaseAllowance(
            _freParams.exchangeContract,
            baseTokenAmount
        );
        //buy DT
        fre.buyDT(
            _freParams.exchangeId,
            1e18, // we always take 1 dt
            baseTokenAmount,
            _freParams.marketFeeAddress,
            _freParams.swapMarketFee
        );
        require(
            balanceOf(address(this)) >= 1e18,
            "Unable to buy DT from FixedRate"
        );
        // collect the basetoken from fixedrate and sent it
        (, , , , , , , , , , uint256 btBalance, ) = fre.getExchange(
            _freParams.exchangeId
        );
        if (btBalance > 0) {
            //record income
            add_revenue(block.number, btBalance);
            fre.collectBT(_freParams.exchangeId, btBalance);
        }
    }

    /**
     * @dev buyFromFreAndOrder
     *      Buys 1 DT from the FRE and then startsOrder, while burning that DT
     */
    function buyFromFreAndOrder(
        OrderParams calldata _orderParams,
        FreParams calldata _freParams
    ) external nonReentrant {
        //first buy 1.0 DT
        buyFromFre(_freParams);
        //we need the following because startOrder expects msg.sender to have dt
        _transfer(address(this), msg.sender, 1e18);
        //startOrder and burn it
        startOrder(
            _orderParams.consumer,
            _orderParams.serviceIndex,
            _orderParams._providerFee,
            _orderParams._consumeMarketFee
        );
    }

    /**
     * @dev buyFromDispenserAndOrder
     *      Gets DT from dispenser and then startsOrder, while burning that DT
     */
    function buyFromDispenserAndOrder(
        OrderParams calldata _orderParams,
        address dispenserContract
    ) external nonReentrant {
        uint256 amount = 1e18;
        //get DT
        IDispenser(dispenserContract).dispense(
            address(this),
            amount,
            msg.sender
        );
        require(
            balanceOf(address(msg.sender)) >= amount,
            "Unable to get DT from Dispenser"
        );
        //startOrder and burn it
        startOrder(
            _orderParams.consumer,
            _orderParams.serviceIndex,
            _orderParams._providerFee,
            _orderParams._consumeMarketFee
        );
    }

    /**
     * @dev isERC20Deployer
     *      returns true if address has deployERC20 role
     */
    function isERC20Deployer(address user) public view returns (bool) {
        return (
            IERC721Template(_erc721Address).getPermissions(user).deployERC20
        );
    }

    /**
     * @dev getFixedRates
     *      Returns the list of fixedRateExchanges created for this datatoken
     */
    function getFixedRates() public view returns (fixedRate[] memory) {
        return (fixedRateExchanges);
    }

    /**
     * @dev getDispensers
     *      Returns the list of dispensers created for this datatoken
     */
    function getDispensers() public view returns (address[] memory) {
        return (dispensers);
    }

    function _pullUnderlying(
        address erc20,
        address from,
        address to,
        uint256 amount
    ) internal {
        uint256 balanceBefore = IERC20(erc20).balanceOf(to);
        IERC20(erc20).safeTransferFrom(from, to, amount);
        require(
            IERC20(erc20).balanceOf(to) >= balanceBefore.add(amount),
            "Transfer amount is too low"
        );
    }

    // ------------ PREDICTOOR ------------
    function is_valid_subscription(address user) public view returns (bool) {
        return subscriptions[user].expires <= block.number ? false : true;
    }

    function epoch() public view returns (uint256) {
        return block.number / blocks_per_epoch;
    }

    function rail_blocknum_to_slot(
        uint256 blocknum
    ) public view returns (uint256) {
        return (blocknum / blocks_per_epoch) * blocks_per_epoch;
    }

    function blocknum_is_on_a_slot(
        uint256 blocknum
    ) public view returns (bool) {
        // a slot == beginning/end of an epoch
        return blocknum == rail_blocknum_to_slot(blocknum);
    }

    function soonest_block_to_predict() public view returns (uint256) {
        uint256 slotted_blocknum = rail_blocknum_to_slot(block.number);

        uint256 _blocknum;
        if (slotted_blocknum == block.number) {
            _blocknum = slotted_blocknum + blocks_per_epoch;
        } else {
            _blocknum = slotted_blocknum + 2 * blocks_per_epoch;
        }
        return _blocknum;
    }

    function submitted_predval(
        uint256 blocknum,
        address predictoor
    ) public view blocknumOnSlot(blocknum) returns (bool) {
        return predobjs[blocknum][predictoor].predictoor != address(0);
    }

    function get_agg_predval(
        uint256 blocknum
    ) public view blocknumOnSlot(blocknum) returns (uint256, uint256) {
        require(is_valid_subscription(msg.sender), "Not valid subscription");
        return (agg_predvals_numer[blocknum], agg_predvals_denom[blocknum]);
    }

    function get_subscription_revenue_at_block(
        uint256 blocknum
    ) public view blocknumOnSlot(blocknum) returns (uint256) {
        return (subscription_revenue_at_block[blocknum]);
    }

    function get_prediction(
        uint256 blocknum,
        address predictoor
    )
        public
        view
        blocknumOnSlot(blocknum)
        returns (Prediction memory prediction)
    {
        if (msg.sender != predictoor) {
            require(blocknum > soonest_block_to_predict(), "too early to view");
        }
        //allow predictoors to see their own submissions
        require(
            is_valid_subscription(msg.sender) || msg.sender == predictoor,
            "Not valid subscription"
        );
        prediction = predobjs[blocknum][predictoor];
    }

    // ----------------------- MUTATING FUNCTIONS -----------------------

    function submit_predval(
        bool predval,
        uint256 stake,
        uint256 blocknum
    ) external blocknumOnSlot(blocknum) {
        require(blocknum > soonest_block_to_predict(), "too late to submit");
        require(!submitted_predval(blocknum, msg.sender), "already submitted");
        require(paused == false, "paused");

        Prediction memory predobj = Prediction(
            predval,
            stake,
            msg.sender,
            false
        );

        predobjs[blocknum][msg.sender] = predobj;

        // safe transfer stake
        IERC20(stake_token).safeTransferFrom(msg.sender, address(this), stake);

        // update agg_predvals
        agg_predvals_numer[blocknum] += stake * (predval ? 1 : 0);
        agg_predvals_denom[blocknum] += stake;
    }

    function payout(
        uint256 blocknum,
        address predictoor_addr
    ) external blocknumOnSlot(blocknum) nonReentrant {
        Prediction memory predobj = get_prediction(blocknum, predictoor_addr);
        require(predobj.paid == false, "already paid");

        // if OPF hasn't submitted trueval in truval_submit_timeout days
        // refund stake to predictoor and cancel round
        if (
            block.number > blocknum + truval_submit_timeout_block &&
            !truval_submitted[blocknum]
        ) {
            IERC20(stake_token).safeTransfer(predobj.predictoor, predobj.stake);
            predobj.paid = true;
            return;
        }

        require(truval_submitted[blocknum], "trueval not submitted");
        require(truevals[blocknum] == predobj.predval, "wrong prediction");

        uint256 swe = truevals[blocknum]
            ? agg_predvals_numer[blocknum]
            : agg_predvals_denom[blocknum] - agg_predvals_numer[blocknum];
        uint256 payout_amt = (predobj.stake *
            agg_predvals_denom[blocknum] *
            get_subscription_revenue_at_block(blocknum)) / swe;

        IERC20(stake_token).safeTransferFrom(
            address(this),
            predobj.predictoor,
            payout_amt
        );
        predobj.paid = true;
    }

    // ----------------------- ADMIN FUNCTIONS -----------------------
    function pause_predictions() external onlyERC20Deployer {
        paused = !paused;
    }

    function submit_trueval(
        uint256 blocknum,
        bool trueval
    ) external blocknumOnSlot(blocknum) onlyERC20Deployer {
        // TODO, is onlyERC20Deployer the right modifier?
        require(blocknum < soonest_block_to_predict(), "too early to submit");
        truevals[blocknum] = trueval;
        truval_submitted[blocknum] = true;
    }

    function update_seconds(
        uint256 s_per_block,
        uint256 s_per_epoch,
        uint256 s_per_subscription,
        uint256 _truval_submit_timeout
    ) external onlyERC20Deployer {
        _update_seconds(
            s_per_block,
            s_per_epoch,
            s_per_subscription,
            _truval_submit_timeout
        );
    }

    // ----------------------- INTERNAL FUNCTIONS -----------------------

    function _update_seconds(
        uint256 s_per_block,
        uint256 s_per_epoch,
        uint256 s_per_subscription,
        uint256 _truval_submit_timeout
    ) internal {
        require(s_per_subscription % s_per_block == 0);
        require(s_per_epoch % s_per_block == 0);

        blocks_per_epoch = s_per_epoch / s_per_block;
        blocks_per_subscription = s_per_subscription / s_per_block;
        truval_submit_timeout_block = _truval_submit_timeout / s_per_block;
    }

    function add_revenue(uint256 blocknum, uint256 amount) internal {
        blocknum = rail_blocknum_to_slot(blocknum);
        // for loop and add revenue for blocks_per_epoch blocks
        for (uint256 i = 0; i < blocks_per_subscription; i++) {
            subscription_revenue_at_block[blocknum + blocks_per_epoch] +=
                amount /
                blocks_per_subscription;
        }
    }
}
