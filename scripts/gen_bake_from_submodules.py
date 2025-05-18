from pathlib import Path
import typer
from typing import Dict, List, Any

app = typer.Typer()

DEFAULT_MCP_DIR = Path(__file__).parent.parent / "mcp"
DEFAULT_OUTPUT_FILE = Path(__file__).parent.parent / "docker-bake.hcl"


def find_submodules_with_dockerfile(mcp_dir: Path) -> List[Path]:
    """Return a list of submodule directories under mcp_dir that contain a Dockerfile."""
    return [d for d in mcp_dir.iterdir() if d.is_dir() and (d / "Dockerfile").exists()]


def build_hcl_data(submodules: List[Path]) -> Dict:
    """Build the HCL data structure for docker-bake.hcl generation."""
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
    return hcl_data


def hcl_dump(data: Dict[str, Any]) -> str:
    """Convert the HCL data structure to a string in HCL format."""

    def dump_variable_block(variable_dict: Dict[str, Any]) -> List[str]:
        lines = []
        for var_name, var_val in variable_dict.items():
            lines.append(f'variable "{var_name}" {{')
            for subk, subv in var_val.items():
                lines.append(f'    {subk} = "{subv}"')
            lines.append("}")
            lines.append("")
        return lines

    def dump_group_block(group_dict: Dict[str, Any]) -> List[str]:
        # Only support one group, output as group "name" { ... }
        lines = []
        for group_name, group_val in group_dict.items():
            lines.append(f'group "{group_name}" {{')
            for subk, subv in group_val.items():
                if isinstance(subv, list):
                    lines.append(
                        f'    {subk} = [{", ".join([f"\"{i}\"" for i in subv])}]'
                    )
                else:
                    lines.append(f'    {subk} = "{subv}"')
            lines.append("}")
            lines.append("")
        return lines

    def dump_target_block(target_dict: Dict[str, Any]) -> List[str]:
        # Output each target as target "name" { ... }
        lines = []
        for target_name, target_val in target_dict.items():
            lines.append(f'target "{target_name}" {{')
            for subk, subv in target_val.items():
                if isinstance(subv, list):
                    lines.append(
                        f'    {subk} = [{", ".join([f"\"{i}\"" for i in subv])}]'
                    )
                else:
                    lines.append(f'    {subk} = "{subv}"')
            lines.append("}")
            lines.append("")
        return lines

    lines = []
    if "group" in data:
        lines.extend(dump_group_block(data["group"]))
    if "variable" in data:
        lines.extend(dump_variable_block(data["variable"]))
    if "target" in data:
        lines.extend(dump_target_block(data["target"]))
    return "\n".join(lines)


@app.command()
def main(
    mcp_dir: Path = typer.Option(DEFAULT_MCP_DIR, help="Path to the mcp directory"),
    output_file: Path = typer.Option(
        DEFAULT_OUTPUT_FILE, help="Path to output docker-bake.hcl"
    ),
):
    """Generate a docker-bake.hcl file based on submodules under the mcp directory."""
    submodules = find_submodules_with_dockerfile(mcp_dir)
    hcl_data = build_hcl_data(submodules)
    hcl_str = hcl_dump(hcl_data)
    with output_file.open("w") as f:
        f.write(hcl_str)
    typer.echo(f"docker-bake.hcl generated at {output_file}")


if __name__ == "__main__":
    app()
