#!/bin/bash
set -ex

CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: $CONFIG_FILE not found"
    exit 1
fi

# read mcp.json
MCP_JSON="mcp.json"

if [ ! -f "$MCP_JSON" ]; then
    echo "Error: $MCP_JSON not found"
    exit 1
fi

# apply to claude_desktop_config.json
cp "$MCP_JSON" "$CONFIG_FILE"

# restart claude
killall -9 Claude
open -a Claude