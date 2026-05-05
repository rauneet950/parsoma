/**
 * ens_update.js — Update soul_fingerprint and soul_stage text records on Sepolia.
 *
 * Called by curator.py after each accepted fragment:
 *   node ens_update.js <fingerprint> <stage>
 *
 * Requires .env in the axl/ root with PRIVATE_KEY set.
 */

require("dotenv").config({ path: "../.env" });
const { ethers } = require("ethers");

const RPC_URL  = "https://ethereum-sepolia-rpc.publicnode.com";
const ENS_NAME = "soul-elon.eth";
const RESOLVER = "0xE99638b40E4Fff0129D56f03b55b6bbC4BBE49b5";

const RESOLVER_ABI = [
  "function setText(bytes32 node, string key, string value) external",
];

async function main() {
  const [fingerprint, stage] = process.argv.slice(2);
  if (!fingerprint || !stage) {
    console.error("Usage: node ens_update.js <fingerprint> <stage>");
    process.exit(1);
  }

  const provider = new ethers.JsonRpcProvider(RPC_URL);
  const wallet   = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
  const resolver = new ethers.Contract(RESOLVER, RESOLVER_ABI, wallet);
  const node     = ethers.namehash(ENS_NAME);

  const tx1 = await resolver.setText(node, "soul_fingerprint", fingerprint);
  await tx1.wait();
  console.log(`[ENS] soul_fingerprint updated — tx: ${tx1.hash}`);

  const tx2 = await resolver.setText(node, "soul_stage", stage);
  await tx2.wait();
  console.log(`[ENS] soul_stage = ${stage} — tx: ${tx2.hash}`);
}

main().catch(e => { console.error("[ENS ERROR]", e.message); process.exit(1); });
