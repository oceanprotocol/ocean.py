// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
pragma solidity 0.8.12;

//import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
//import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

//import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
//import "OpenZeppelin/openzeppelin-contracts@4.2.0/contracts/access/Ownable.sol";
import '@openzeppelin/contracts/access/Ownable.sol';
import "../interfaces/IDFRewards.sol";

contract DFRewards is Ownable, ReentrancyGuard, IDFRewards {
    using SafeERC20 for IERC20;

    // token address => user address => balance
    mapping(address => mapping(address => uint256)) balances;
    mapping(address => uint256) allocated;
    //mapping(address => bool) live_strategies;
    address[] public live_strategies;

    // Caller calls token.safeApprove(contract_addr, sum(values)),
    // then it calls this function. Anyone can call this, if can they fund it!
    function allocate(
        address[] calldata _tos,
        uint256[] calldata _values,
        address tokenAddress
    ) external returns (bool) {
        require(_tos.length == _values.length, "Lengths must match");

        uint256 total_value = 0.0;
        for (uint256 i = 0; i < _values.length; i += 1) {
            require(_tos[i] != address(0), "Address invalid");
            require(_values[i] > 0, "Value invalid");
            balances[tokenAddress][_tos[i]] += _values[i];
            total_value += _values[i];
        }

        uint256 _before = IERC20(tokenAddress).balanceOf(address(this));
        IERC20(tokenAddress).safeTransferFrom(
            msg.sender,
            address(this),
            total_value
        );
        uint256 _after = IERC20(tokenAddress).balanceOf(address(this));
        require(_after - _before == total_value, "Not enough tokens");

        allocated[tokenAddress] = allocated[tokenAddress] + total_value;

        emit Allocated(_tos, _values, tokenAddress);
        return true;
    }

    function claimable(address _to, address tokenAddress)
        public
        view
        returns (uint256)
    {
        return balances[tokenAddress][_to];
    }

    function _claim(
        address _to,
        address tokenAddress,
        address _receiver
    ) internal returns (uint256) {
        uint256 amt = balances[tokenAddress][_to];
        if (amt == 0) {
            return 0;
        }
        balances[tokenAddress][_to] = 0;
        IERC20(tokenAddress).safeTransfer(_receiver, amt);
        allocated[tokenAddress] = allocated[tokenAddress] - amt;
        emit Claimed(_to, amt, tokenAddress);
        return amt;
    }

    // Others claim on behalf of recipient
    function claimFor(address _to, address tokenAddress)
        public
        nonReentrant
        returns (uint256)
    {
        return _claim(_to, tokenAddress, _to);
    }

    // Strategies can claim on behalf of recipient
    function claimForStrat(address _to, address tokenAddress)
        public
        nonReentrant
        returns (uint256)
    {
        require(tx.origin == _to, "Caller doesn't match");
        require(isStrategy(msg.sender), "Caller must be a strategy");

        return _claim(_to, tokenAddress, msg.sender);
    }

    /*
     * @dev Withdraw any ERC20 token from the contract, cannot withdraw the allocated amount.
     * @param _amount The amount of tokens to withdraw.
     * @param _token The token address to withdraw.
     */
    function withdrawERCToken(uint256 amount, address _token)
        external
        onlyOwner
    {
        require(
            IERC20(_token).balanceOf(address(this)) - amount >=
                allocated[_token],
            "Cannot withdraw allocated token"
        );
        IERC20(_token).transfer(msg.sender, amount);
    }

    /**
     * @dev isStrategy
     *      Returns true if strategy exists in the list
     *  @param _strategy address Strategy address to be checked
     */
    function isStrategy(address _strategy) public view returns (bool) {
        for (uint256 i = 0; i < live_strategies.length; i++) {
            if (live_strategies[i] == _strategy) return true;
        }
        return false;
    }

    /**
     * @dev addStrategy
     *      Adds a new strategy
     *  @param _strategy address Strategy address to be added
     */
    function addStrategy(address _strategy) external onlyOwner {
        if (!isStrategy(_strategy)) {
            live_strategies.push(_strategy);
            emit StrategyAdded(_strategy);
        }
    }

    /**
     * @dev retireStrategy
     *      Removes an existng strategy
     *  @param _strategy address Strategy address to be removed
     */
    function retireStrategy(address _strategy) external onlyOwner {
        require(_strategy != address(0), "Invalid strategy address");
        uint256 i;
        for (i = 0; i < live_strategies.length; i++) {
            if (live_strategies[i] == _strategy) break;
        }
        if (i < live_strategies.length) {
            live_strategies[i] = live_strategies[live_strategies.length - 1];
            live_strategies.pop();
            emit StrategyRetired(_strategy);
        }
    }

    // Don't allow eth transfers
    fallback() external {
        revert("Invalid ether transfer");
    }
}
