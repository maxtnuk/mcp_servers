.PHONY: build gen_mcp_server_json all

gen_mcp_server_json:
	python3 scripts/gen_mcp_server_json.py --output mcp.json

build: 
	python3 scripts/gen_bake_from_submodules.py
	docker buildx bake

all: build gen_mcp_server_json

apply_claude_for_mac: all
	CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

	scripts/claud_apply.sh
