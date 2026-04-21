# FleetOps

> The Operating System for Governed Human-Agent Work

FleetOps is a centralized control plane that connects existing AI coding agents (Claude Code, Codex, Copilot, Kilo, OpenCode, etc.) and adds governance, human-in-the-loop controls, full observability, and immutable evidence stores.

## What Makes FleetOps Different

- **Human-in-the-loop at any stage** — not just approval gates
- **Full hierarchy for humans and agents** — explicit roles and escalation paths
- **Complete observability** — every LLM call, prompt, and cost tracked
- **Immutable evidence** — append-only logs, cryptographically signed
- **Cross-provider normalization** — heterogeneous agent fleets, unified governance

## Quick Start

```bash
# Clone the repo
git clone https://github.com/LunarPerovskite/FleetOps.git
cd FleetOps

# Install dependencies (coming soon)
pip install -r requirements.txt

# Run the FleetOps platform (coming soon)
fleetops serve
```

## Architecture

See [FLEETOPS_SPEC.md](FLEETOPS_SPEC.md) for the full platform specification.

## Status

🚧 **MVP in development** — Phase 1 targets: Auth system, agent connectors (Claude Code + Codex), task model, HiTL approval engine, evidence store, cost tracking, basic dashboard.

## License

MIT License — see [LICENSE](LICENSE)

## Contact

- GitHub: [LunarPerovskite/FleetOps](https://github.com/LunarPerovskite/FleetOps)
- Created by: Juan Esteban Mosquera + AI co-architect
