"""
CLI tool for scaffolding new FastAPI projects from this starter template
Reference: https://docs.python.org/3/library/argparse.html
"""
import argparse
import shutil
import sys
from pathlib import Path
from importlib import resources


def get_template_files() -> list[Path]:
    """
    Get list of template files to copy when scaffolding a new project.
    
    Returns paths relative to the package root that should be included.
    """
    # Files and directories to include in the template
    # These are relative to the project root
    template_files = [
        "app",
        "alembic",
        "alembic.ini",
        "pyproject.toml",
        "README.md",
        "runtime.txt",
        "vercel.json",
    ]
    
    # Convert to Path objects
    return [Path(f) for f in template_files]


def copy_template_files(source_dir: Path, dest_dir: Path, project_name: str) -> None:
    """
    Copy template files from source to destination, customizing as needed.
    
    Args:
        source_dir: Source directory containing template files
        dest_dir: Destination directory for new project
        project_name: Name of the new project (for customization)
    """
    template_files = get_template_files()
    
    # Create destination directory
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy each file/directory
    for item in template_files:
        source_path = source_dir / item
        dest_path = dest_dir / item
        
        if not source_path.exists():
            print(f"Warning: Template file {item} not found, skipping...")
            continue
        
        if source_path.is_dir():
            # Copy directory recursively
            shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
        else:
            # Copy file
            shutil.copy2(source_path, dest_path)
    
    # Customize pyproject.toml with new project name
    pyproject_path = dest_dir / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        # Replace package name with project name (sanitized)
        sanitized_name = project_name.lower().replace(" ", "_").replace("-", "_")
        content = content.replace('name = "fastapi-auth-starter"', f'name = "{sanitized_name}"')
        pyproject_path.write_text(content)
    
    print(f"✓ Created new FastAPI project: {dest_dir}")


def find_package_root() -> Path:
    """
    Find the root directory containing template files.
    
    When installed as a package, template files are in the package's shared-data.
    In development mode, they're in the project root.
    """
    try:
        # First, try development mode (current file's parent's parent)
        package_file = Path(__file__).resolve()
        dev_root = package_file.parent.parent
        
        # Check if we're in development mode
        if (dev_root / "app").exists() and (dev_root / "alembic").exists():
            return dev_root
        
        # If installed as a package, template files are in shared-data
        # Try to find them using importlib.resources
        try:
            import importlib.resources
            # Try to access a known file from the package
            package = importlib.resources.files("fastapi_auth_starter")
            # Look for shared data files
            # In hatchling, shared-data files are at the package root level
            # But we need to check the actual installation location
            
            # Alternative: check site-packages for the package
            import site
            for site_dir in site.getsitepackages():
                # Check if package is installed here
                package_dir = Path(site_dir) / "fastapi_auth_starter"
                if package_dir.exists():
                    # Shared data might be in the package directory or parent
                    # Hatchling puts shared-data in the package root
                    # So app/ and alembic/ should be in site_dir/fastapi_auth_starter/
                    if (package_dir / "app").exists():
                        return package_dir
                    # Or they might be in the parent (site_dir)
                    if (Path(site_dir) / "app").exists():
                        return Path(site_dir)
        except Exception:
            pass
        
        # Fallback: try to find in common installation locations
        # This handles editable installs and other scenarios
        return dev_root
        
    except Exception as e:
        print(f"Error finding package root: {e}")
        # Final fallback
        return Path(__file__).resolve().parent.parent


def init_project(project_name: str, target_dir: Path | None = None) -> None:
    """
    Initialize a new FastAPI project from this starter template.
    
    Args:
        project_name: Name of the new project
        target_dir: Target directory (defaults to current directory/project_name)
    """
    if target_dir is None:
        target_dir = Path.cwd() / project_name
    
    # Check if target directory already exists
    if target_dir.exists():
        print(f"Error: Directory {target_dir} already exists!")
        sys.exit(1)
    
    # Find the template source directory
    source_dir = find_package_root()
    
    if not source_dir.exists():
        print(f"Error: Could not find template source directory!")
        sys.exit(1)
    
    print(f"Creating new FastAPI project '{project_name}' from template...")
    print(f"Source: {source_dir}")
    print(f"Destination: {target_dir}")
    
    # Copy template files
    copy_template_files(source_dir, target_dir, project_name)
    
    print("\n✓ Project created successfully!")
    print(f"\nNext steps:")
    print(f"  1. cd {target_dir}")
    print(f"  2. Create a .env file with your configuration")
    print(f"  3. Run: uv sync")
    print(f"  4. Run: uv run alembic upgrade head")
    print(f"  5. Run: uv run uvicorn app.main:app --reload")


def main() -> None:
    """
    Main CLI entry point.
    Handles command-line arguments and dispatches to appropriate functions.
    """
    parser = argparse.ArgumentParser(
        description="FastAPI Auth Starter - Scaffold new FastAPI projects",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fastapi-auth-starter init my-api
  fastapi-auth-starter init my-api --dir /path/to/projects
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new FastAPI project")
    init_parser.add_argument(
        "project_name",
        help="Name of the new project"
    )
    init_parser.add_argument(
        "--dir",
        type=Path,
        help="Target directory (defaults to current directory/project_name)"
    )
    
    args = parser.parse_args()
    
    if args.command == "init":
        target_dir = args.dir / args.project_name if args.dir else None
        init_project(args.project_name, target_dir)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

