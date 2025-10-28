#!/bin/bash

# MCP Diagnostic Script for Game Watcher
# This script helps diagnose MCP (Model Context Protocol) server issues

echo "🔍 MCP Diagnostic Report"
echo "========================"
echo

# Check uvx availability
echo "📦 uvx Installation:"
echo "  System uvx: $(which uvx 2>/dev/null || echo 'NOT FOUND')"
echo "  Local uvx:  $(ls -la /home/vscode/.local/bin/uvx 2>/dev/null || echo 'NOT FOUND')"
echo "  uvx version: $(uvx --version 2>/dev/null || echo 'ERROR')"
echo

# Check PATH
echo "🛣️  PATH Configuration:"
echo "  Current PATH: $PATH"
echo "  uvx in PATH: $(echo $PATH | grep -o '/home/vscode/.local/bin' || echo 'MISSING')"
echo

# Test MCP server
echo "🖥️  MCP Server Test:"
echo "  Testing mcp-server-fetch:"
uvx mcp-server-fetch --help >/dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "    ✅ mcp-server-fetch is working"
else
    echo "    ❌ mcp-server-fetch failed"
fi

# Check VS Code settings
echo "⚙️  VS Code Configuration:"
if [ -f "/workspaces/game-watcher/.vscode/settings.json" ]; then
    echo "    ✅ .vscode/settings.json exists"
    if grep -q "mcp.servers" /workspaces/game-watcher/.vscode/settings.json; then
        echo "    ✅ MCP servers configured"
    else
        echo "    ⚠️  No MCP servers configured"
    fi
else
    echo "    ❌ .vscode/settings.json missing"
fi

echo
echo "🎯 Quick Fixes:"
echo "  • Restart VS Code if uvx was just installed"
echo "  • Check VS Code extensions for MCP support"
echo "  • Ensure /usr/local/bin/uvx symlink exists"
echo "  • Verify .vscode/settings.json MCP configuration"