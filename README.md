# Sudosu 🚀

[![PyPI version](https://badge.fury.io/py/sudosu.svg)](https://badge.fury.io/py/sudosu)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Downloads](https://pepy.tech/badge/sudosu)](https://pepy.tech/project/sudosu)

**Your AI Coworker - Right in Your Terminal**

Sudosu gives you AI coworkers that can actually get work done. Unlike chatbots that just talk, these teammates can read your files, write code, create documents, connect to all your tools (Gmail, Calendar, GitHub, Linear, Slack), and run commands - all while you stay in control.

**No more hopping between tools.** Your AI coworker does it all.

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
Go through my slack channel product-team and summarise the messages from yesterday 
and plan tickets in Linear
```

## Features

- 🤖 **AI Coworkers**: Create specialized coworkers with specific personalities and capabilities
- 🔌 **Tool Integrations**: Connect to Gmail, Calendar, GitHub, Linear, Slack, and more
- 📝 **File Operations**: Coworkers can read and write files in your repository
- 🔄 **Real-time Streaming**: See responses as they're generated
- 🔒 **Local Execution**: File operations happen on your machine, keeping data secure
- ⚡ **Action-Oriented**: Your coworkers don't just answer questions — they take action

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
