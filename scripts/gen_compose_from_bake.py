import hcl2
from pathlib import Path
import yaml
import typer

app = typer.Typer()

BASE_DIR = Path(__file__).parent.parent.resolve()


# Helper to extract EXPOSE port from Dockerfile
def get_expose_port(dockerfile_path):
    dockerfile_path = Path(dockerfile_path)
    if not dockerfile_path.exists():
        return None
    with dockerfile_path.open("r") as f:
        for line in f:
            if line.strip().startswith("EXPOSE"):
                parts = line.strip().split()
                if len(parts) > 1:
                    return parts[1]
    return None


@app.command()
def main(
    bake_file: Path = typer.Option(
        BASE_DIR / "docker-bake.hcl",
        help="Path to docker-bake.hcl file",
    ),
    output: Path = typer.Option(
        BASE_DIR / "server" / "docker-compose.yaml",
        help="Output path for docker-compose.yaml",
    ),
    dockerfiles_base: Path = typer.Option(
        BASE_DIR, help="Base directory for Dockerfile contexts"
    ),
    group_name: str = typer.Option(
        "default", help="Group name to generate compose for"
    ),
):
    with bake_file.open("r") as f:
        bake = hcl2.load(f)

    services = {}

    # Parse group_targets (group "name" { ... })
    group_targets = []
    for group_block in bake.get("group", []):
        for each_group_name, group_val in group_block.items():
            if each_group_name == group_name:
                group_targets = group_val.get("targets", [])
                break
        if group_targets:
            break

    # Parse variables (variable "TAG" { ... })
    variables = {}
    for v in bake.get("variable", []):
        for var_name, var_val in v.items():
            variables[var_name] = var_val.get("default", "")
    tag = variables.get("TAG", "latest")

    # Parse targets (target "name" { ... })
    targets = {}
    for t in bake.get("target", []):
        for target_name, target_val in t.items():
            targets[target_name] = target_val

    for target_name in group_targets:
        target = targets.get(target_name)
        if not target:
            continue
        context = target["context"]
        dockerfile = target.get("dockerfile", "Dockerfile")
        tags = target.get("tags", [])
        image = tags[0].replace("${TAG}", tag) if tags else f"{target_name}:{tag}"
        container_name = target_name
        dockerfile_path = dockerfiles_base / context / dockerfile
        expose_port = get_expose_port(dockerfile_path)

        service = {
            "image": image,
            "container_name": container_name,
            "network_mode": "host",
        }
        if expose_port:
            service["ports"] = [f"{expose_port}:{expose_port}"]
        services[target_name] = service

    compose = {"services": services}
    with output.open("w") as f:
        yaml.dump(compose, f, default_flow_style=False, sort_keys=False)
    typer.echo(f"docker-compose.yaml generated at {output}")


if __name__ == "__main__":
    app()
