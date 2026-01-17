# Sudosu 🚀

**Terminal-based AI Agent Platform**

Create and interact with custom AI agents that run on a hosted backend but use your local terminal as a client. Agents have access to your repository for read/write operations.

## Installation

```bash
pip install sudosu
```

## Quick Start

```bash
# Initialize Sudosu
sudosu init

# Start interactive session
sudosu

# Create an agent
/agent create writer

# Use the agent
@writer help me write a blog on AI in 2026
```

## Features

-  **Custom Agents**: Create agents with specific personalities and capabilities
- 📝 **File Operations**: Agents can read and write files in your repository
- 🔄 **Real-time Streaming**: See agent responses as they're generated
- 🔒 **Local Execution**: File operations happen on your machine, keeping data secure
- 🎯 **Skills Integration**: Extend agents with reusable skills (coming soon)

## Configuration

### Environment Modes

Sudosu supports **dev** and **prod** modes for easy switching between local and production backends:

```bash
# Development mode (local backend)
export SUDOSU_MODE=dev
sudosu

# Production mode (default)
export SUDOSU_MODE=prod
sudosu

# Or switch within CLI
/config mode dev   # Switch to development
/config mode prod  # Switch to production
```

See [ENVIRONMENT_SETUP.md](./ENVIRONMENT_SETUP.md) for detailed configuration options.

### Configuration Files

Sudosu stores configuration in `~/.sudosu/`:

```
~/.sudosu/
├── config.yaml     # API keys, backend URL, preferences, mode
├── agents/         # Global agent definitions
└── skills/         # Global skills library
```

Project-specific configuration goes in `<repo>/.sudosu/`.

## License

MIT
