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

**Zero configuration required.** Just install and run:

```bash
# Install
pip install sudosu

# Start using immediately - no setup needed!
sudosu
```

That's it! Sudosu works out of the box with our hosted backend.

### Example Tasks

```bash
# Start interactive session
sudosu

# Then just ask:
> Summarize the unread emails in my inbox
> Create a Linear ticket for the bug we discussed
> Check my calendar for tomorrow and draft a prep email
> Go through #product-team slack and summarize yesterday's messages
```

### Connect Your Tools

```bash
# Inside sudosu, connect integrations:
/connect gmail      # Connect Gmail
/connect slack      # Connect Slack  
/connect linear     # Connect Linear
/connect github     # Connect GitHub
/connect notion     # Connect Notion
```

## Features

- 🚀 **Zero Config**: Install and run - works immediately with hosted backend
- 🤖 **AI Coworkers**: Create specialized coworkers with specific personalities and capabilities
- 🔌 **Tool Integrations**: Connect to Gmail, Calendar, GitHub, Linear, Slack, Notion, and more
- 📝 **File Operations**: Coworkers can read and write files in your repository
- 🔄 **Real-time Streaming**: See responses as they're generated
- 🔒 **Local Execution**: File operations happen on your machine, keeping data secure
- ⚡ **Action-Oriented**: Your coworkers don't just answer questions — they take action

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/connect <service>` | Connect an integration (gmail, slack, etc.) |
| `/disconnect <service>` | Disconnect an integration |
| `/integrations` | Show connected integrations |
| `/agent create <name>` | Create a new agent |
| `/agent list` | List available agents |
| `/clear` | Clear the screen |
| `/quit` | Exit sudosu |

## Configuration (Optional)

Sudosu works out of the box, but you can customize it:

### Environment Modes

```bash
# Development mode (local backend)
export SUDOSU_MODE=dev
sudosu

# Production mode (default - uses hosted backend)
export SUDOSU_MODE=prod
sudosu

# Or switch within CLI
/config mode dev   # Switch to development
/config mode prod  # Switch to production
```

### Configuration Files

Sudosu stores configuration in `~/.sudosu/`:

```
~/.sudosu/
└── config.yaml     # Preferences and mode settings
```

Project-specific configuration goes in `<your-repo>/.sudosu/`.

## Requirements

- Python 3.10+
- Internet connection (for hosted backend)

## Links

- **Website**: [trysudosu.com](https://trysudosu.com)
- **Issues**: [GitHub Issues](https://github.com/csakash/sudosu-cli/issues)

## License

MIT
