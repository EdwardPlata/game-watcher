#!/bin/bash

# Game Watcher Development Environment Setup Script

echo "🚀 Setting up Game Watcher development environment..."

# Install uv and uvx (modern Python package manager)
echo "📦 Installing uv and uvx..."
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv/uvx to PATH for current session
export PATH="$HOME/.local/bin:$PATH"

# Add uv/uvx to PATH permanently
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

# Create system-wide links for uvx/uv (fixes MCP server issues)
sudo ln -sf $HOME/.local/bin/uvx /usr/local/bin/uvx
sudo ln -sf $HOME/.local/bin/uv /usr/local/bin/uv

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file from template..."
    cp config.env .env
    echo "✅ Created .env file. Please update it with your API keys."
fi

# Initialize the database
echo "🗄️ Initializing database..."
python -c "from utils.database import DatabaseManager; DatabaseManager()"

echo "✅ Development environment setup complete!"
echo ""
echo "🎯 Quick Start:"
echo "  • Start web server: python web_server.py"
echo "  • Collect data: python main.py fetch"
echo "  • View docs: http://localhost:8000/docs"
echo ""
echo "🔧 Tools available:"
echo "  • uv: $(uv --version)"
echo "  • uvx: $(uvx --version)"