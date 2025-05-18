from pathlib import Path
import typer

app = typer.Typer()

DEFAULT_MCP_DIR = Path(__file__).parent.parent / "mcp"
DEFAULT_OUTPUT_FILE = Path(__file__).parent.parent / "docker-bake.hcl"


def hcl_dump(data):
    # hcl2 does not support dumping, so we need to write a helper for HCL output
    def dump_block(key, value, indent=0):
        pad = " " * indent
        if isinstance(value, dict):
            lines = [f"{pad}{key} {{"]
            for k, v in value.items():
                lines.extend(dump_block(k, v, indent + 4))
            lines.append(f"{pad}}}")
            return lines
        elif isinstance(value, list):
            if all(isinstance(i, str) for i in value):
                return [f'{pad}{key} = [{", ".join([f"\"{i}\"" for i in value])}]']
            else:
                lines = []
                for v in value:
                    lines.extend(dump_block(key, v, indent))
                return lines
        elif isinstance(value, str):
            return [f'{pad}{key} = "{value}"']
        else:
            return [f"{pad}{key} = {value}"]

    lines = []
    for k, v in data.items():
        lines.extend(dump_block(k, v))
        lines.append("")
    return "\n".join(lines)


@app.command()
def main(
    mcp_dir: Path = typer.Option(DEFAULT_MCP_DIR, help="Path to the mcp directory"),
    output_file: Path = typer.Option(
        DEFAULT_OUTPUT_FILE, help="Path to output docker-bake.hcl"
    ),
):
    submodules = [
        d for d in mcp_dir.iterdir() if d.is_dir() and (d / "Dockerfile").exists()
    ]
    target_names = [d.name for d in submodules]

    hcl_data = {
        "group": {"default": {"targets": target_names}},
        "variable": {"TAG": {"default": "latest"}},
        "target": {},
    }
    for d in submodules:
        hcl_data["target"][d.name] = {
            "context": f"./mcp/{d.name}",
            "dockerfile": "Dockerfile",
            "tags": [f"{d.name}:${{TAG}}"],
        }

    hcl_str = hcl_dump(hcl_data)
    with output_file.open("w") as f:
        f.write(hcl_str)
    typer.echo(f"docker-bake.hcl generated at {output_file}")


if __name__ == "__main__":
    app()
