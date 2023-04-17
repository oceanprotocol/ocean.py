pragma solidity 0.8.12;
// Copyright BigchainDB GmbH and Ocean Protocol contributors
// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
// Code is Apache-2.0 and docs are CC-BY-4.0
import "../interfaces/IERC721Template.sol";
import "../utils/ERC721/ERC721.sol";
import "../utils/ERC725/ERC725Ocean.sol";
import "../utils/ERC721/IERC721Enumerable.sol";
import "@openzeppelin/contracts/utils/Create2.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "../interfaces/IFactory.sol";
import "../interfaces/IERC20Template.sol";
import "../utils/ERC721RolesAddress.sol";



contract ERC721Template is
    ERC721("Template", "TemplateSymbol"),
    ERC721RolesAddress,
    ERC725Ocean,
    ReentrancyGuard
{
    
    string private _name;
    string private _symbol;
    //uint256 private tokenId = 1;
    bool private initialized;
    bool public hasMetaData;
    string public metaDataDecryptorUrl;
    string public metaDataDecryptorAddress;
    uint8 public metaDataState;
    address private _tokenFactory;
    address[] private deployedERC20List;
    uint8 private constant templateId = 1;
    mapping(address => bool) private deployedERC20;
    bool public transferable;

    //stored here only for ABI reasons
    event TokenCreated(
        address indexed newTokenAddress,
        address indexed templateAddress,
        string name,
        string symbol,
        uint256 cap,
        address creator
    );  
    event MetadataCreated(
        address indexed createdBy,
        uint8 state,
        string decryptorUrl,
        bytes flags,
        bytes data,
        bytes32 metaDataHash,
        uint256 timestamp,
        uint256 blockNumber
    );
    event MetadataUpdated(
        address indexed updatedBy,
        uint8 state,
        string decryptorUrl,
        bytes flags,
        bytes data,
        bytes32 metaDataHash,
        uint256 timestamp,
        uint256 blockNumber
    );
    event MetadataValidated(
        address indexed validator,
        bytes32 metaDataHash,
        uint8 v, 
        bytes32 r, 
        bytes32 s
    );
    event MetadataState(
        address indexed updatedBy,
        uint8 state,
        uint256 timestamp,
        uint256 blockNumber
    );

    event TokenURIUpdate(
        address indexed updatedBy,
        string tokenURI,
        uint256 tokenID,
        uint256 timestamp,
        uint256 blockNumber
    );

    modifier onlyNFTOwner() {
        require(msg.sender == ownerOf(1), "ERC721Template: not NFTOwner");
        _;
    }

     
    /**
     * @dev initialize
     *      Calls private _initialize function. Only if contract is not initialized.
            This function mints an NFT (tokenId=1) to the owner and add owner as Manager Role
     * @param owner NFT Owner
     * @param name_ NFT name
     * @param symbol_ NFT Symbol
     * @param tokenFactory NFT factory address
     * @param additionalERC20Deployer address of additionalERC20Deployer
     * @param additionalMetaDataUpdater address of additionalMetaDataUpdater
     * @param tokenURI tokenURI
     * @param transferable_ if set to false, this NFT is non-transferable
     
     @return boolean
     */

    function initialize(
        address owner,
        string calldata name_,
        string calldata symbol_,
        address tokenFactory,
        address additionalERC20Deployer,
        address additionalMetaDataUpdater,
        string memory tokenURI,
        bool transferable_
    ) external returns (bool) {
        require(
            !initialized,
            "ERC721Template: token instance already initialized"
        );
        if(additionalERC20Deployer != address(0))
            _addToCreateERC20List(additionalERC20Deployer);
        if(additionalMetaDataUpdater != address(0))
            _addToMetadataList(additionalMetaDataUpdater);
        bool initResult = 
            _initialize(
                owner,
                name_,
                symbol_,
                tokenFactory,
                tokenURI,
                transferable_
            );
        //register all erc721 interfaces
        registerAllInterfaces();
        //register erc725 interfaces
        _registerInterface(_INTERFACE_ID_ERC725X);
        _registerInterface(_INTERFACE_ID_ERC725Y);
        return(initResult);
    }

    /**
     * @dev _initialize
     *      Calls private _initialize function. Only if contract is not initialized.
     *       This function mints an NFT (tokenId=1) to the owner
     *       and add owner as Manager Role (Roles admin)
     * @param owner NFT Owner
     * @param name_ NFT name
     * @param symbol_ NFT Symbol
     * @param tokenFactory NFT factory address
     * @param tokenURI tokenURI for token 1
     
     @return boolean
     */

    function _initialize(
        address owner,
        string memory name_,
        string memory symbol_,
        address tokenFactory,
        string memory tokenURI,
        bool transferable_
    ) internal returns (bool) {
        require(
            owner != address(0),
            "ERC721Template:: Invalid minter,  zero address"
        );
        
        _name = name_;
        _symbol = symbol_;
        _tokenFactory = tokenFactory;
        defaultBaseURI = "";
        initialized = true;
        hasMetaData = false;
        transferable = transferable_;
        _safeMint(owner, 1);
        _addManager(owner);

        // we add the nft owner to all other roles (so that doesn't need to make multiple transactions)
        Roles storage user = permissions[owner];
        user.updateMetadata = true;
        user.deployERC20 = true;
        user.store = true;
        // no need to push to auth since it has been already added in _addManager()
        _setTokenURI(1, tokenURI);
        
        return initialized;
    }

    /**
     * @dev setTokenURI
     *      sets tokenURI for a tokenId
     * @param tokenId token ID
     * @param tokenURI token URI
     */
    function setTokenURI(uint256 tokenId, string memory tokenURI) public {
        require(msg.sender == ownerOf(tokenId), "ERC721Template: not NFTOwner");
        _setTokenURI(tokenId, tokenURI);
        emit TokenURIUpdate(msg.sender, tokenURI, tokenId,
            /* solium-disable-next-line */
            block.timestamp,
            block.number);
    }

    

    /**
     * @dev setMetaDataState
     *      Updates metadata state
     * @param _metaDataState metadata state
     */
    function setMetaDataState(uint8 _metaDataState) public {
        require(
            permissions[msg.sender].updateMetadata,
            "ERC721Template: NOT METADATA_ROLE"
        );
        metaDataState = _metaDataState;
        emit MetadataState(msg.sender, _metaDataState,
            /* solium-disable-next-line */
            block.timestamp,
            block.number);
    }

    struct metaDataProof {
        address validatorAddress;
        uint8 v; // v of validator signed message
        bytes32 r; // r of validator signed message
        bytes32 s; // s of validator signed message
    }
    /**
     * @dev setMetaData
     *     
             Creates or update Metadata for Aqua(emit event)
             Also, updates the METADATA_DECRYPTOR key
     * @param _metaDataState metadata state
     * @param _metaDataDecryptorUrl decryptor URL
     * @param _metaDataDecryptorAddress decryptor public key
     * @param flags flags used by Aquarius
     * @param data data used by Aquarius
     * @param _metaDataHash hash of clear data (before the encryption, if any)
     * @param _metadataProofs optional signatures of entitys who validated data (before the encryption, if any)
     */
    function setMetaData(uint8 _metaDataState, string calldata _metaDataDecryptorUrl
        , string calldata _metaDataDecryptorAddress, bytes calldata flags, 
        bytes calldata data,bytes32 _metaDataHash, metaDataProof[] memory _metadataProofs) external {
        require(
            permissions[msg.sender].updateMetadata,
            "ERC721Template: NOT METADATA_ROLE"
        );
        _setMetaData(_metaDataState, _metaDataDecryptorUrl, _metaDataDecryptorAddress,flags, 
        data,_metaDataHash, _metadataProofs);
    }

    function _setMetaData(uint8 _metaDataState, string calldata _metaDataDecryptorUrl
        , string calldata _metaDataDecryptorAddress, bytes calldata flags, 
        bytes calldata data,bytes32 _metaDataHash, metaDataProof[] memory _metadataProofs) internal {
        metaDataState = _metaDataState;
        metaDataDecryptorUrl = _metaDataDecryptorUrl;
        metaDataDecryptorAddress = _metaDataDecryptorAddress;
        if(!hasMetaData){
            emit MetadataCreated(msg.sender, _metaDataState, _metaDataDecryptorUrl,
            flags, data, _metaDataHash, 
            /* solium-disable-next-line */
            block.timestamp,
            block.number);
            hasMetaData = true;
        }
        else
            emit MetadataUpdated(msg.sender, metaDataState, _metaDataDecryptorUrl,
            flags, data, _metaDataHash,
            /* solium-disable-next-line */
            block.timestamp,
            block.number);
        //check proofs and emit an event for each proof
        require(_metadataProofs.length <= 50, 'Too Many Proofs');
        bytes memory prefix = "\x19Ethereum Signed Message:\n32";
        for (uint256 i = 0; i < _metadataProofs.length; i++) {
            if(_metadataProofs[i].validatorAddress != address(0)){
                    bytes32 prefixedHash = keccak256(abi.encodePacked(prefix, _metaDataHash));
                    address signer = ecrecover(prefixedHash,
                    _metadataProofs[i].v, _metadataProofs[i].r, _metadataProofs[i].s);
                    require(signer == _metadataProofs[i].validatorAddress, "Invalid proof signer");
            }
            emit MetadataValidated(_metadataProofs[i].validatorAddress, 
            _metaDataHash, 
            _metadataProofs[i].v, _metadataProofs[i].r, _metadataProofs[i].s);
        }
    }

    struct metaDataAndTokenURI {
        uint8 metaDataState;
        string metaDataDecryptorUrl;
        string metaDataDecryptorAddress;
        bytes flags;
        bytes data;
        bytes32 metaDataHash;
        uint256 tokenId;
        string tokenURI;
        metaDataProof[] metadataProofs;
    }

    /**
     * @dev setMetaDataAndTokenURI
     *       Helper function to improve UX
             Calls setMetaData & setTokenURI
     * @param _metaDataAndTokenURI   metaDataAndTokenURI struct
     */
    function setMetaDataAndTokenURI(metaDataAndTokenURI calldata _metaDataAndTokenURI) external {
        require(
            permissions[msg.sender].updateMetadata,
            "ERC721Template: NOT METADATA_ROLE"
        );
        _setMetaData(_metaDataAndTokenURI.metaDataState, _metaDataAndTokenURI.metaDataDecryptorUrl, 
            _metaDataAndTokenURI.metaDataDecryptorAddress, _metaDataAndTokenURI.flags, 
            _metaDataAndTokenURI.data, _metaDataAndTokenURI.metaDataHash, _metaDataAndTokenURI.metadataProofs);
        
        setTokenURI(_metaDataAndTokenURI.tokenId, _metaDataAndTokenURI.tokenURI);
        
    }
    /**
     * @dev getMetaData
     *      Returns metaDataState, metaDataDecryptorUrl, metaDataDecryptorAddress
     */
    function getMetaData() external view returns (string memory, string memory, uint8, bool){
        return (metaDataDecryptorUrl, metaDataDecryptorAddress, metaDataState, hasMetaData);
    } 


    /**
     * @dev createERC20
     *        ONLY user with deployERC20 permission (assigned by Manager) can call it
             Creates a new ERC20 datatoken.
            It also adds initial minting and fee management permissions to custom users.

     * @param _templateIndex ERC20Template index 
     * @param strings refers to an array of strings
     *                      [0] = name
     *                      [1] = symbol
     * @param addresses refers to an array of addresses
     *                     [0]  = minter account who can mint datatokens (can have multiple minters)
     *                     [1]  = feeManager initial feeManager for this DT
     *                     [2]  = publishing Market Address
     *                     [3]  = publishing Market Fee Token
     * @param uints  refers to an array of uints
     *                     [0] = cap_ the total ERC20 cap
     *                     [1] = publishing Market Fee Amount
     * @param bytess  refers to an array of bytes
     *                     Currently not used, usefull for future templates
     
     @return ERC20 token address
     */

    function createERC20(
        uint256 _templateIndex,
        string[] calldata strings,
        address[] calldata addresses,
        uint256[] calldata uints,
        bytes[] calldata bytess
    ) external nonReentrant returns (address ) {
        require(
            permissions[msg.sender].deployERC20,
            "ERC721Template: NOT ERC20DEPLOYER_ROLE"
        );

        address token = IFactory(_tokenFactory).createToken(
            _templateIndex,
            strings,
            addresses,
            uints,
            bytess
        );

        deployedERC20[token] = true;

        deployedERC20List.push(token);
        return token;
    }

    /**
     * @dev isERC20Deployer
     * @return true if the account has ERC20 Deploy role
     */
    function isERC20Deployer(address account) external view returns (bool) {
        return permissions[account].deployERC20;
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
     * @dev isInitialized
     *      It checks whether the contract is initialized.
     * @return true if the contract is initialized.
     */

    function isInitialized() external view returns (bool) {
        return initialized;
    }

    /**
     * @dev addManager
     *      Only NFT Owner can add a new manager (Roles admin)
     *      There can be multiple minters
     * @param _managerAddress new manager address
     */

    function addManager(address _managerAddress) external onlyNFTOwner {
        _addManager(_managerAddress);
    }

    /**
     * @dev removeManager
     *      Only NFT Owner can remove a manager (Roles admin)
     *      There can be multiple minters
     * @param _managerAddress new manager address
     */


    function removeManager(address _managerAddress) external onlyNFTOwner {
        _removeManager(_managerAddress);
    }

     /**
     * @notice Executes any other smart contract. 
                Is only callable by the Manager.
     *
     *
     * @param _operation the operation to execute: CALL = 0; DELEGATECALL = 1; CREATE2 = 2; CREATE = 3;
     * @param _to the smart contract or address to interact with. 
     *          `_to` will be unused if a contract is created (operation 2 and 3)
     * @param _value the value of ETH to transfer
     * @param _data the call data, or the contract data to deploy
    **/

    function executeCall(
        uint256 _operation,
        address _to,
        uint256 _value,
        bytes calldata _data
    ) external payable onlyManager {
        execute(_operation, _to, _value, _data);
    }


      /**
     * @dev setNewData
     *       ONLY user with store permission (assigned by Manager) can call it
            This function allows to set any arbitrary key-value into the 725 standard
     *      There can be multiple store updaters
     * @param _key key (see 725 for standard (keccak256)) 
        Data keys, should be the keccak256 hash of a type name.
        e.g. keccak256('ERCXXXMyNewKeyType') is 0x6935a24ea384927f250ee0b954ed498cd9203fc5d2bf95c735e52e6ca675e047

     * @param _value data to store at that key
     */


    function setNewData(bytes32 _key, bytes calldata _value) external {
        require(
            permissions[msg.sender].store,
            "ERC721Template: NOT STORE UPDATER"
        );
        setData(_key, _value);
    }

       /**
     * @dev setDataERC20
     *      ONLY callable FROM the ERC20Template and BY the corresponding ERC20Deployer
            This function allows to store data with a preset key (keccak256(ERC20Address)) into NFT 725 Store
     * @param _key keccak256(ERC20Address) see setData into ERC20Template.sol
     * @param _value data to store at that key
     */


    function setDataERC20(bytes32 _key, bytes calldata _value) external {
        require(
            deployedERC20[msg.sender],
            "ERC721Template: NOT ERC20 Contract"
        );
        setData(_key, _value);
    }


    /**
     * @dev cleanPermissions
     *      Only NFT Owner  can call it.
     *      This function allows to remove all ROLES at erc721 level: 
     *              Managers, ERC20Deployer, MetadataUpdater, StoreUpdater
     *      Permissions at erc20 level stay.
     */
    
    function cleanPermissions() external onlyNFTOwner {
        _cleanPermissions();
        //make sure that owner still has permissions
        _addManager(ownerOf(1));
    }


  
     /**
     * @dev transferFrom 
     *      Used for transferring the NFT, can be used by an approved relayer
            Even if we only have 1 tokenId, we leave it open as arguments for being a standard ERC721
            @param from nft owner
            @param to nft receiver
            @param tokenId tokenId (1)
     */

    function transferFrom(
        address from,
        address to,
        uint256 tokenId
    ) external {
        require(transferable, "ERC721Template: Is non transferable");
        require(tokenId == 1, "ERC721Template: Cannot transfer this tokenId");
        _cleanERC20Permissions(getAddressLength(deployedERC20List));
        _cleanPermissions();
        _addManager(to);
          // we add the nft owner to all other roles (so that doesn't need to make multiple transactions)
        Roles storage user = permissions[to];
        user.updateMetadata = true;
        user.deployERC20 = true;
        user.store = true;
        // no need to push to auth since it has been already added in _addManager()
        _transferFrom(from, to, tokenId);
        
    }

    /**
     * @dev safeTransferFrom 
     *      Used for transferring the NFT, can be used by an approved relayer
            Even if we only have 1 tokenId, we leave it open as arguments for being a standard ERC721
            @param from nft owner
            @param to nft receiver
            @param tokenId tokenId (1)
     */

    function safeTransferFrom(address from, address to,uint256 tokenId) external {
        require(transferable, "ERC721Template: Is non transferable");
        require(tokenId == 1, "ERC721Template: Cannot transfer this tokenId");
        _cleanERC20Permissions(getAddressLength(deployedERC20List));
        _cleanPermissions();
        _addManager(to);
        // we add the nft owner to all other roles (so that doesn't need to make multiple transactions)
        Roles storage user = permissions[to];
        user.updateMetadata = true;
        user.deployERC20 = true;
        user.store = true;
        // no need to push to auth since it has been already added in _addManager()
        _safeTransferFrom(from, to, tokenId, "");
        
    }

      /**
     * @dev getAddressLength
     *      It returns the array lentgh
            @param array address array we want to get length
     * @return length
     */


    function getAddressLength(address[] memory array)
        private
        pure
        returns (uint256)
    {
        return array.length;
    }

      /**
     * @dev _cleanERC20Permissions
     *      Internal function used to clean permissions at ERC20 level when transferring the NFT
            @param length lentgh of the deployedERC20List 
     */

    function _cleanERC20Permissions(uint256 length) internal {
        for (uint256 i = 0; i < length; i++) {
            IERC20Template(deployedERC20List[i]).cleanFrom721();
        }
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
     *      transfers all the accumlated ether the ownerOf
     */
    function withdrawETH() 
        external 
        payable
    {
        payable(ownerOf(1)).transfer(address(this).balance);
    }

    function getTokensList() external view returns (address[] memory) {
        return deployedERC20List;
    }
    
    function isDeployed(address datatoken) external view returns (bool) {
        return deployedERC20[datatoken];
    }

    function setBaseURI(string memory _baseURI) external onlyNFTOwner {
            defaultBaseURI = _baseURI;
    }
}