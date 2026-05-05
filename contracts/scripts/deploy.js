import { ethers } from "ethers";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import dotenv from "dotenv";
dotenv.config({ path: new URL("../../.env", import.meta.url).pathname });

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const artifact = JSON.parse(
  fs.readFileSync(path.join(__dirname, "../artifacts/contracts/PersomaPayment.sol/PersomaPayment.json"), "utf8")
);

const USDC        = "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238";
const PLATFORM    = "0x6D5EE220E17C9cF3c48b9eaDefC17Bc5449365D9";
const SOUL_HOLDER = "0x343aEE40Cc47A2817ACf319c51B5324Cd5ACf262";
const CLAWS = [
  "0x67A816a10978A415d1EA5f909D501E1b77E1b59f",
  "0xF656916b8cd41FCd554F8183505C9Bee840bf094",
  "0x2e43f8dAb3eA6DF7112e24808693e20507a5e99f",
];
const WEIGHTS = [1, 1, 1];

const provider = new ethers.JsonRpcProvider("https://ethereum-sepolia-rpc.publicnode.com");
const pk = process.env.PRIVATE_KEY.startsWith("0x") ? process.env.PRIVATE_KEY : `0x${process.env.PRIVATE_KEY}`;
const wallet = new ethers.Wallet(pk, provider);
console.log("Deploying with:", wallet.address);

const factory = new ethers.ContractFactory(artifact.abi, artifact.bytecode, wallet);
const contract = await factory.deploy(USDC, PLATFORM, SOUL_HOLDER, CLAWS, WEIGHTS);
console.log("Tx sent:", contract.deploymentTransaction().hash);
await contract.waitForDeployment();

const address = await contract.getAddress();
console.log("PersomaPayment deployed to:", address);

const config = {
  soul_id: "soul-elon-musk",
  ens_name: "soul-elon.eth",
  testnet: "sepolia",
  chain_id: "11155111",
  usdc_address: USDC,
  contract_address: address,
  platform_wallet: PLATFORM,
  soul_nft_holder_wallet: SOUL_HOLDER,
  riya_wallet: "0xCeB025753bEcED3A89c4583F5fADc6387DA57EB2",
  claws: [
    { id: "claw-a", wallet: CLAWS[0] },
    { id: "claw-b", wallet: CLAWS[1] },
    { id: "claw-c", wallet: CLAWS[2] },
  ],
};

const configPath = path.join(__dirname, "../../config.json");
fs.writeFileSync(configPath, JSON.stringify(config, null, 2));
console.log("config.json written to:", configPath);
