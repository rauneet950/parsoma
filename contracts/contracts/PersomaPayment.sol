// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface IERC20 {
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function transfer(address to, uint256 amount) external returns (bool);
}

contract PersomaPayment {
    IERC20 public immutable usdc;
    address public immutable platform;
    address public immutable soulNFTHolder;
    address[] public claws;
    uint256[] public weights;
    uint256 public totalWeight;

    event Payment(address indexed payer, uint256 amount);

    constructor(
        address _usdc,
        address _platform,
        address _soulNFTHolder,
        address[] memory _claws,
        uint256[] memory _weights
    ) {
        require(_claws.length == _weights.length, "length mismatch");
        usdc = IERC20(_usdc);
        platform = _platform;
        soulNFTHolder = _soulNFTHolder;
        claws = _claws;
        weights = _weights;
        uint256 tw;
        for (uint256 i = 0; i < _weights.length; i++) tw += _weights[i];
        totalWeight = tw;
    }

    function pay(uint256 amount) external {
        require(amount > 0, "zero amount");
        usdc.transferFrom(msg.sender, address(this), amount);

        uint256 platformCut = (amount * 20) / 100;
        uint256 soulCut = (amount * 10) / 100;
        uint256 clawPool = amount - platformCut - soulCut;

        usdc.transfer(platform, platformCut);
        usdc.transfer(soulNFTHolder, soulCut);

        for (uint256 i = 0; i < claws.length; i++) {
            uint256 clawCut = (clawPool * weights[i]) / totalWeight;
            usdc.transfer(claws[i], clawCut);
        }

        emit Payment(msg.sender, amount);
    }

    function getClaws() external view returns (address[] memory, uint256[] memory) {
        return (claws, weights);
    }
}
