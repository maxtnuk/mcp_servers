import hcl2
import json
from pathlib import Path
import typer

app = typer.Typer()

DEFAULT_BAKE_FILE = Path(__file__).parent.parent / "docker-bake.hcl"
DEFAULT_ENVS_DIR = Path(__file__).parent.parent / "envs"
DEFAULT_CONFIG_FILE = Path(__file__).parent.parent / "config" / "mcp_config.json"
DEFAULT_CUSTOM_FILE = Path(__file__).parent.parent / "config" / "custom.json"


def parse_env_file(env_path: Path):
    env_dict = {}
    if not env_path.exists():
        return env_dict
    with env_path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env_dict[key.strip()] = value.strip()
    return env_dict


def load_blacklist(config_path: Path):
    if not config_path.exists():
        return set()
    with config_path.open() as f:
        config = json.load(f)
    return set(config.get("blacklist", []))


def load_custom(custom_path: Path):
    if not custom_path.exists():
        return {}
    with custom_path.open() as f:
        return json.load(f)


@app.command()
def main(
    bake_file: Path = typer.Option(DEFAULT_BAKE_FILE, help="Path to docker-bake.hcl"),
    group_name: str = typer.Option("default", help="Group name to use"),
    envs_dir: Path = typer.Option(DEFAULT_ENVS_DIR, help="Path to envs directory"),
    config_file: Path = typer.Option(
        DEFAULT_CONFIG_FILE, help="Path to mcp_config.json"
    ),
    custom_file: Path = typer.Option(DEFAULT_CUSTOM_FILE, help="Path to custom.json"),
    output: Path = typer.Option(None, help="Output JSON file (default: stdout"),
):
    blacklist = load_blacklist(config_file)
    custom = load_custom(custom_file)

    with bake_file.open() as f:
        bake = hcl2.load(f)

    # Parse group_targets
    group_targets = []
    for group_block in bake.get("group", []):
        for each_group_name, group_val in group_block.items():
            if each_group_name == group_name:
                group_targets = group_val.get("targets", [])
                break
        if group_targets:
            break

    # Parse targets
    targets = {}
    for t in bake.get("target", []):
        for target_name, target_val in t.items():
            targets[target_name] = target_val

    # Parse variables (variable "TAG" { ... })
    variables = {}
    for v in bake.get("variable", []):
        for var_name, var_val in v.items():
            variables[var_name] = var_val.get("default", "")
    tag = variables.get("TAG", "latest")

    mcp_servers = {}
    for name in group_targets:
        if name in blacklist:
            continue
        target = targets.get(name)
        if not target:
            continue
        tags = target.get("tags", [])
        image = tags[0].replace("${TAG}", tag) if tags else f"{name}:{tag}"
        # Parse env file for this service
        env_path = envs_dir / name / ".env"
        env_dict = parse_env_file(env_path)
        args = [
            "run",
            "-i",
            "--name",
            name,
            "--rm",
        ]
        for k in env_dict:
            args.extend(["-e", k])
        args.append(image)
        mcp_servers[name] = {
            "command": "docker",
            "args": args,
            "env": env_dict,
        }

    # Merge custom.json (custom entries override generated ones)
    mcp_servers.update(custom)

    output_dict = {"mcpServers": mcp_servers}
    json_str = json.dumps(output_dict, indent=2)
    if output:
        with output.open("w") as f:
            f.write(json_str)
        typer.echo(f"Wrote JSON to {output}")
    else:
        typer.echo(json_str)


if __name__ == "__main__":
    app()
