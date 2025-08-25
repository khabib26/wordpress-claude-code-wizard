#!/bin/bash

# Create .mcp.json file for Playwright MCP configuration
cat > .mcp.json << 'EOF'
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"],
      "env": {}
    }
  }
}
EOF

echo "✅ Created .mcp.json with Playwright MCP configuration"
echo "When you run 'claude' in this directory, you'll be prompted to approve the Playwright MCP."