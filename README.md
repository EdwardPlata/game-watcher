# Game Watcher

A comprehensive game monitoring and data analysis application with integrated MCP (Model Context Protocol) servers for enhanced development capabilities.

## Overview

Game Watcher is designed to monitor, analyze, and provide insights into gaming data and metrics. The project leverages multiple MCP servers to provide powerful tools for data engineering, software engineering, and personal productivity.

## Features

- 🎮 Game monitoring and analytics
- 📊 Data engineering capabilities
- 🔧 Software development tools
- 🤖 AI-powered insights via MCP integration
- 📁 Advanced file and repository management
- 🌐 Web content fetching and processing
- 🧠 Persistent memory and knowledge graphs
- ⏰ Time and timezone management

## MCP Server Integration

This project includes a comprehensive MCP server configuration that provides the following capabilities:

### GitHub Server
- Repository management and operations
- Issue and pull request handling
- GitHub API integration
- Code review and collaboration tools

### Filesystem Server
- Secure file operations with access controls
- File reading, writing, and management
- Directory operations and navigation

### Git Server
- Local git repository operations
- Status, log, diff, and commit operations
- Branch management and version control

### Fetch Server
- Web content fetching and conversion
- Clean text/markdown extraction for AI processing
- API endpoint integration

### Memory Server
- Knowledge graph-based persistent memory
- Cross-conversation information storage
- Entity and relationship management

### Time Server
- Current time retrieval in various timezones
- Time conversion between timezones
- Time-related calculations and operations

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- Python 3.8+ (for some MCP servers)
- Git
- VS Code (recommended for MCP integration)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/EdwardPlata/game-watcher.git
cd game-watcher
```

2. Install dependencies:
```bash
npm install
```

3. Set up MCP servers (if using VS Code):
   - The `.vscode/mcp.json` file is already configured
   - Install required dependencies:
   ```bash
   # Install npm-based servers
   npm install -g @modelcontextprotocol/server-filesystem
   npm install -g @modelcontextprotocol/server-memory
   
   # Install Python-based servers (using uvx)
   pip install uv
   uvx mcp-server-git
   uvx mcp-server-fetch
   uvx mcp-server-time
   ```

### Configuration

The MCP servers are pre-configured in `.vscode/mcp.json`. You may need to adjust paths and settings based on your environment:

- **Filesystem server**: Currently set to `/workspaces` - update to your preferred root directory
- **Git server**: Currently set to `/workspaces/game-watcher` - update to your project path

## Usage

### Development Environment

If using VS Code with MCP support:
1. Open the project in VS Code
2. The MCP servers will automatically load based on the configuration
3. Use AI assistance with enhanced capabilities from all integrated servers

### Available Tools

Through the MCP integration, you have access to:
- **100+ GitHub operations** (issues, PRs, repos, workflows, etc.)
- **13 filesystem operations** (read, write, search, manage files)
- **12 git operations** (status, commit, branch, merge, etc.)
- **8 memory operations** (knowledge graphs, entities, relations)
- **Web fetching** capabilities for external data
- **Time management** tools for scheduling and logging

## Project Structure

```
game-watcher/
├── .vscode/
│   └── mcp.json          # MCP server configuration
├── src/                  # Source code (to be developed)
├── data/                 # Data storage and processing
├── docs/                 # Documentation
├── tests/                # Test files
├── package.json          # Node.js dependencies
└── README.md            # This file
```

## Development Roadmap

- [ ] Core game monitoring functionality
- [ ] Data pipeline for game metrics
- [ ] Analytics dashboard
- [ ] Real-time monitoring capabilities
- [ ] AI-powered insights and recommendations
- [ ] API integrations for popular gaming platforms
- [ ] Custom game data connectors

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP framework
- [GitHub MCP Server](https://github.com/github/github-mcp-server) for GitHub integration
- [MCP Servers Repository](https://github.com/modelcontextprotocol/servers) for additional server implementations

## Support

For questions and support:
- Create an issue on GitHub
- Check the documentation in the `docs/` directory
- Review MCP server documentation for specific tool capabilities