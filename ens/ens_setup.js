/**
 * ens_setup.js — Register soul-elon.eth on Sepolia and set initial text records.
 *
 * Run once:
 *   node ens_setup.js
 *
 * Requires .env in the axl/ root with PRIVATE_KEY set.
 */

require("dotenv").config({ path: "../.env" });
const { ethers } = require("ethers");

const RPC_URL  = "https://ethereum-sepolia-rpc.publicnode.com";
const ENS_NAME = "soul-elon.eth";
const LABEL    = "soul-elon";

// Sepolia ENS contract addresses (ens-contracts staging branch, deployments/sepolia/)
const CONTROLLER = "0xfb3cE5D01e0f33f41DbB39035dB9745962F1f968";
const RESOLVER   = "0xE99638b40E4Fff0129D56f03b55b6bbC4BBE49b5";
const REGISTRY   = "0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e";

const CONTROLLER_ABI = [
  "function available(string label) external view returns (bool)",
  "function rentPrice(string label, uint256 duration) external view returns (tuple(uint256 base, uint256 premium))",
  "function makeCommitment(tuple(string label, address owner, uint256 duration, bytes32 secret, address resolver, bytes[] data, uint8 reverseRecord, bytes32 referrer) registration) external pure returns (bytes32)",
  "function commit(bytes32 commitment) external",
  "function register(tuple(string label, address owner, uint256 duration, bytes32 secret, address resolver, bytes[] data, uint8 reverseRecord, bytes32 referrer) registration) external payable",
];

const RESOLVER_ABI = [
  "function setText(bytes32 node, string key, string value) external",
];

const REGISTRY_ABI = [
  "function owner(bytes32 node) external view returns (address)",
];

async function main() {
  const provider   = new ethers.JsonRpcProvider(RPC_URL);
  const wallet     = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
  const controller = new ethers.Contract(CONTROLLER, CONTROLLER_ABI, wallet);
  const registry   = new ethers.Contract(REGISTRY, REGISTRY_ABI, provider);

  console.log("Wallet:", wallet.address);

  // Check if already registered
  const node         = ethers.namehash(ENS_NAME);
  const currentOwner = await registry.owner(node);
  if (currentOwner !== ethers.ZeroAddress) {
    console.log(`${ENS_NAME} already registered (owner: ${currentOwner})`);
    console.log("Skipping registration — setting text records only...");
    await setTextRecords(wallet, "genesis", "embryo");
    return;
  }

  const available = await controller.available(LABEL);
  if (!available) {
    console.error(`${ENS_NAME} is not available.`);
    process.exit(1);
  }

  const duration = 365 * 24 * 60 * 60; // 1 year
  const { base, premium } = await controller.rentPrice(LABEL, duration);
  const price = base + premium;
  console.log(`Rent price: ${ethers.formatEther(price)} ETH`);

  const secret = ethers.hexlify(ethers.randomBytes(32));

  const registration = {
    label: LABEL,
    owner: wallet.address,
    duration,
    secret,
    resolver: RESOLVER,
    data: [],
    reverseRecord: 0,
    referrer: ethers.ZeroHash,
  };

  const commitment = await controller.makeCommitment(registration);

  console.log("Committing...");
  const commitTx = await controller.commit(commitment);
  await commitTx.wait();
  console.log("Committed. Waiting 65 seconds (ENS minCommitmentAge)...");
  await new Promise(r => setTimeout(r, 65_000));

  console.log("Registering...");
  const registerTx = await controller.register(registration, { value: price * 110n / 100n });
  await registerTx.wait();
  console.log(`Registered ${ENS_NAME}! tx: ${registerTx.hash}`);

  await setTextRecords(wallet, "genesis", "embryo");
}

async function setTextRecords(wallet, fingerprint, stage) {
  const resolver = new ethers.Contract(RESOLVER, RESOLVER_ABI, wallet);
  const node     = ethers.namehash(ENS_NAME);

  console.log("Setting text records...");
  const tx1 = await resolver.setText(node, "soul_fingerprint", fingerprint);
  await tx1.wait();
  console.log(`soul_fingerprint = "${fingerprint}" — tx: ${tx1.hash}`);

  const tx2 = await resolver.setText(node, "soul_stage", stage);
  await tx2.wait();
  console.log(`soul_stage = "${stage}" — tx: ${tx2.hash}`);
}

main().catch(e => { console.error(e.message); process.exit(1); });
