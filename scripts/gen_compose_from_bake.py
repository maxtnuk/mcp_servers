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
):
    with bake_file.open("r") as f:
        bake = hcl2.load(f)

    services = {}

    # Parse group_targets
    group = bake.get("group", [{}])[0]
    group_default = group.get("default", [{}])[0]
    group_targets = group_default.get("targets", [])

    # Parse variables
    variables = {}
    for v in bake.get("variable", []):
        for k, val in v.items():
            variables[k] = val[0].get("default", "")
    tag = variables.get("TAG", "latest")

    # Parse targets
    targets = {}
    for t in bake.get("target", []):
        for name, val in t.items():
            targets[name] = val[0]

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
