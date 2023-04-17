// SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
pragma solidity 0.8.12;

interface IDFRewards {
    event Allocated(address[] tos, uint256[] values, address tokenAddress);
    event Claimed(address to, uint256 value, address tokenAddress);
    event StrategyAdded(address strategy);
    event StrategyRetired(address strategy);

    function claimable(address _to, address tokenAddress)
        external
        view
        returns (uint256);

    function claimFor(address _to, address tokenAddress)
        external
        returns (uint256);

    function withdrawERCToken(uint256 amount, address _token) external;

    function claimForStrat(address _to, address tokenAddress)
        external
        returns (uint256);
}
