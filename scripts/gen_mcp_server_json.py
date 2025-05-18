import hcl2
import json
from pathlib import Path
import typer

app = typer.Typer()

DEFAULT_BAKE_FILE = Path(__file__).parent.parent / "docker-bake.hcl"


@app.command()
def main(
    bake_file: Path = typer.Option(DEFAULT_BAKE_FILE, help="Path to docker-bake.hcl"),
    group_name: str = typer.Option("default", help="Group name to use"),
    output: Path = typer.Option(None, help="Output JSON file (default: stdout)"),
):
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
        target = targets.get(name)
        if not target:
            continue
        tags = target.get("tags", [])
        image = tags[0].replace("${TAG}", tag) if tags else f"{target_name}:{tag}"

        args = [
            "run",
            "-i",
            "--rm",
            image,
        ]
        mcp_servers[name] = {
            "command": "docker",
            "args": args,
            "env": {},
        }

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
