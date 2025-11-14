"""
CLI tool for scaffolding new FastAPI projects from this starter template
Reference: https://docs.python.org/3/library/argparse.html
"""
import argparse
import shutil
import sys
from pathlib import Path


def get_template_files() -> list[Path]:
    """
    Get list of template files to copy when scaffolding a new project.
    
    Returns paths relative to the package root that should be included.
    """
    # Files and directories to include in the template
    # These are relative to the project root
    # Note: fastapi_auth_starter/ is excluded - it's only for the package itself
    template_files = [
        "app",
        "alembic",
        "alembic.ini",
        "pyproject.toml",
        "README.md",
        "runtime.txt",
        "vercel.json",
        ".gitignore",  # Include .gitignore if it exists
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
            # Skip silently for optional files like .gitignore
            if item != ".gitignore":
                print(f"Warning: Template file {item} not found, skipping...")
            continue
        
        # Explicitly exclude the package directory
        if item == "fastapi_auth_starter":
            continue
        
        if source_path.is_dir():
            # Copy directory recursively, excluding __pycache__ and .pyc files
            shutil.copytree(
                source_path, 
                dest_path, 
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")
            )
        else:
            # Copy file
            shutil.copy2(source_path, dest_path)
    
    # Create a clean pyproject.toml for standalone application
    pyproject_path = dest_dir / "pyproject.toml"
    if pyproject_path.exists():
        # Read original to extract dependencies
        original_content = pyproject_path.read_text()
        
        # Extract dependencies from original
        import re
        deps_match = re.search(r'dependencies = \[(.*?)\]', original_content, re.DOTALL)
        dev_deps_match = re.search(r'\[project\.optional-dependencies\]\s+dev = \[(.*?)\]', original_content, re.DOTALL)
        
        dependencies = deps_match.group(1).strip() if deps_match else ""
        dev_dependencies = dev_deps_match.group(1).strip() if dev_deps_match else ""
        
        # Sanitize project name
        sanitized_name = project_name.lower().replace(" ", "_").replace("-", "_")
        
        # Create clean pyproject.toml for standalone application
        clean_content = f"""[project]
name = "{sanitized_name}"
version = "0.1.0"
description = "FastAPI application"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
{dependencies}
]

# Development dependencies
[project.optional-dependencies]
dev = [
{dev_dependencies}
]
"""
        pyproject_path.write_text(clean_content)
    
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
        # Hatchling places shared-data files in the package's installation directory
        # We need to find where the package is installed and look for shared-data
        try:
            import site
            import sysconfig
            
            # Get all possible site-packages locations
            site_dirs = site.getsitepackages()
            if hasattr(site, 'getsitepackages'):
                # Also check user site-packages
                try:
                    user_site = site.getusersitepackages()
                    if user_site:
                        site_dirs.append(user_site)
                except AttributeError:
                    pass
            
            # Also check where this package is actually installed
            # The package is at fastapi_auth_starter/__init__.py, so parent is fastapi_auth_starter/
            package_location = Path(__file__).parent
            package_parent = package_location.parent  # This is site-packages or similar
            
            # Hatchling shared-data places files at the site-packages level
            # So if package is at site-packages/fastapi_auth_starter/
            # Shared data is at site-packages/app/, site-packages/alembic/, etc.
            if package_parent.exists():
                # Check if shared-data is at the site-packages level
                if (package_parent / "app").exists() and (package_parent / "alembic").exists():
                    return package_parent
                
                # Also check parent of site-packages (unlikely but possible)
                if package_parent.parent.exists():
                    if (package_parent.parent / "app").exists() and (package_parent.parent / "alembic").exists():
                        return package_parent.parent
            
            # Check standard site-packages locations
            for site_dir in site_dirs:
                site_path = Path(site_dir)
                
                # Check if shared-data is in site-packages root
                if (site_path / "app").exists() and (site_path / "alembic").exists():
                    return site_path
                
                # Check in package directory
                package_dir = site_path / "fastapi_auth_starter"
                if package_dir.exists():
                    # Check parent (shared-data might be at site-packages level)
                    if (site_path / "app").exists():
                        return site_path
                    # Or in package directory itself
                    if (package_dir / "app").exists():
                        return package_dir
                    
                    # Check parent of package (hatchling shared-data location)
                    package_parent = package_dir.parent
                    if (package_parent / "app").exists():
                        return package_parent
                        
        except Exception as e:
            # Log error but continue to fallback
            print(f"Warning: Error checking site-packages: {e}", file=sys.stderr)
        
        # Fallback: use development root
        # This handles editable installs and other scenarios
        return dev_root
        
    except Exception as e:
        print(f"Error finding package root: {e}", file=sys.stderr)
        # Final fallback: use current file's parent's parent
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
    
    # Debug: Verify source directory has required files
    if not (source_dir / "app").exists():
        print(f"Warning: 'app' directory not found at {source_dir / 'app'}", file=sys.stderr)
    if not (source_dir / "alembic").exists():
        print(f"Warning: 'alembic' directory not found at {source_dir / 'alembic'}", file=sys.stderr)
    
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

