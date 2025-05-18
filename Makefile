.PHONY: build generate deploy deploy_down

generate:
	python3 scripts/gen_bake_from_submodules.py
	python3 scripts/gen_compose_from_bake.py

build: generate
	docker buildx bake

deploy: build
	cd deploy && docker compose up -d

deploy_down:
	cd deploy && docker compose down