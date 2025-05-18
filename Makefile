.PHONY: build generate gen_mcp_server_json deploy deploy_down	

generate:
	python3 scripts/gen_bake_from_submodules.py
	python3 scripts/gen_compose_from_bake.py

gen_mcp_server_json:
	python3 scripts/gen_mcp_server_json.py

build: 
	python3 scripts/gen_bake_from_submodules.py
	docker buildx bake

deploy: build
	python3 scripts/gen_compose_from_bake.py
	cd deploy && docker compose up -d

deploy_down:
	cd deploy && docker compose down