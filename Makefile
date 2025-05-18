.PHONY: build gen_mcp_server_json all

gen_mcp_server_json:
	python3 scripts/gen_mcp_server_json.py --output mcp.json

build: 
	python3 scripts/gen_bake_from_submodules.py
	docker buildx bake

all: build gen_mcp_server_json
