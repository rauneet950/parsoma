# Parsoma

A decentralized protocol where independent AI agents collaboratively build, verify, and monetize living digital personalities of public figures — entirely over peer-to-peer infrastructure.

**Built for ETHGlobal Open Agents Hackathon**

![network cartoon](assets/distributed-agents-cartoon.png)

## What It Does

Parsoma lets multiple AI agents (called **Claws**) each analyze a different dimension of a public figure's personality — communication style, decision patterns, stance on AI — and contribute structured personality **fragments** over a P2P mesh network. A **Curator** agent receives, validates, and assembles these fragments into a complete **Soul** — a living digital personality identified by an ENS name (e.g., `soul-elon.eth`).

End users can chat with the Soul via an LLM, paying a USDC fee that auto-distributes to all contributing agents proportionally.

## Architecture

```
3 Claw Agents (Python)
    → publish personality fragments to GossipSub topic: soul-elon-musk

1 Curator Agent (Python)
    → subscribes to topic, validates fragments, builds soul-elon.json
    → updates ENS text records on Sepolia after each accepted fragment

Smart Contract (Solidity, Sepolia)
    → receives USDC payment, splits: 20% platform / 10% Soul creator / 70% Claws

End User CLI (Python)
    → resolves soul-elon.eth via ENS → fetches Soul → chats via LLM
```

## Tech Stack

| Component | Technology | Role |
|-----------|-----------|------|
| P2P Network | [Gensyn AXL](https://github.com/gensyn-ai/axl) | Agent-to-agent communication over GossipSub mesh |
| Identity | ENS (Sepolia) | Human-readable Soul identity (`soul-elon.eth`) |
| Payments | Solidity + USDC | Automated 20/10/70 payment distribution |
| Automation | KeeperHub | Guaranteed on-chain payment execution |
| Agents | Python | Claw publishers + Curator subscriber |
| Contracts | Hardhat + ethers.js | Deployment and ENS interaction |

## Project Structure

```
├── claw.py                     # Claw agent — publishes personality fragments
├── curator.py                  # Curator agent — validates, assembles, updates ENS
├── soul-elon.json              # Assembled Soul data (built by Curator)
├── config.json                 # Contract addresses, wallet config
├── contracts/
│   ├── contracts/PersomaPayment.sol   # USDC payment split contract
│   ├── scripts/deploy.js              # Hardhat deploy script
│   └── hardhat.config.js
├── ens/
│   ├── ens_setup.js            # One-time ENS registration
│   └── ens_update.js           # Update fingerprint after each fragment
├── node-config*.json           # AXL node configurations (Curator + 3 Claws)
├── api/                        # AXL HTTP API handlers (Go)
├── internal/                   # AXL network internals (Go)
├── examples/                   # Python client examples + GossipSub library
└── docs/                       # AXL documentation
```

## How to Run

### 1. Start AXL Nodes

```bash
# Build the node
make build

# Terminal 1 — Curator node
./node -config node-config.json

# Terminal 2-4 — Claw nodes
./node -config node-config-2.json
./node -config node-config-3.json
./node -config node-config-4.json
```

### 2. Start Curator Agent

```bash
python3 curator.py
```

### 3. Publish Fragments

```bash
python3 claw.py --id claw-a --port 9012 --dimension communication_style \
    --content "Short punchy sentences. Meme humor mixed with technical depth."

python3 claw.py --id claw-b --port 9022 --dimension stance_on_ai \
    --content "AI is the most transformative technology. Existential risk is real."

python3 claw.py --id claw-c --port 9032 --dimension decision_patterns \
    --content "First principles thinking. Fast iteration. High tolerance for failure."
```

### 4. Verify

- `soul-elon.json` builds in real time
- ENS records update on Sepolia
- Payment contract distributes USDC on interaction

## Payment Split

When an end user pays X USDC to interact with a Soul:

| Recipient | Share | Description |
|-----------|-------|-------------|
| Platform | 20% | Protocol fee |
| Soul Creator | 10% | Person who initiated the Soul |
| Claw Agents | 70% | Split by contribution weight (fragment count) |

## On-Chain (Sepolia Testnet)

| Item | Details |
|------|---------|
| ENS Name | `soul-elon.eth` |
| Payment Contract | [`0xf8C4c7523B31F8CAEB328AB403E75F987aB7460A`](https://sepolia.etherscan.io/address/0xf8C4c7523B31F8CAEB328AB403E75F987aB7460A) |
| USDC (Sepolia) | `0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238` |

## Sponsors

- **Gensyn AXL** — P2P communication between agents
- **ENS** — Soul identity on Ethereum
- **KeeperHub** — Guaranteed on-chain payment execution
- **Uniswap** — Token swap fallback for non-USDC payments

## License

MIT
