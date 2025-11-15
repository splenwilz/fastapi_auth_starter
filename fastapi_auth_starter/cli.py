"""
CLI tool for scaffolding new FastAPI projects from this starter template
Reference: https://docs.python.org/3/library/argparse.html
"""
import argparse
import re
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
        ".env.example",  # Include .env.example template
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
            # Skip silently for optional files like .gitignore and .env.example
            if item not in [".gitignore", ".env.example"]:
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
        try:
            original_content = pyproject_path.read_text(encoding='utf-8')
            print(f"[DEBUG] Read pyproject.toml, length: {len(original_content)} chars", file=sys.stderr)
            # Show first few lines for debugging
            first_lines = '\n'.join(original_content.split('\n')[:15])
            print(f"[DEBUG] First 15 lines of original:\n{first_lines}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not read pyproject.toml: {e}", file=sys.stderr)
            original_content = ""
        
        # Extract dependencies from original using a more robust method
        # Handle dependencies with square brackets like uvicorn[standard]
        def extract_array_content(content: str, key: str) -> list[str]:
            """Extract array content by finding matching brackets."""
            # Find the key and opening bracket
            pattern = rf'{key}\s*=\s*\['
            match = re.search(pattern, content)
            if not match:
                return []
            
            start_pos = match.end()
            bracket_count = 1
            pos = start_pos
            lines = []
            current_line = ""
            in_string = False
            string_char = None
            
            # Parse until we find the matching closing bracket
            while pos < len(content) and bracket_count > 0:
                char = content[pos]
                prev_char = content[pos - 1] if pos > 0 else ''
                
                # Handle string literals (don't count brackets inside strings)
                if char in ('"', "'") and prev_char != '\\':
                    if not in_string:
                        in_string = True
                        string_char = char
                    elif char == string_char:
                        in_string = False
                        string_char = None
                    current_line += char
                elif in_string:
                    # Inside a string, just add the character
                    current_line += char
                elif char == '[':
                    bracket_count += 1
                    current_line += char
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found the closing bracket
                        # Don't add the ']' to current_line, but save current_line if it has content
                        if current_line.strip():
                            lines.append(current_line.strip())
                        break
                    current_line += char
                elif char == '\n':
                    if current_line.strip():
                        lines.append(current_line.strip())
                    current_line = ""
                else:
                    current_line += char
                
                pos += 1
            
            # Clean up lines - remove comments, empty lines, and trailing commas
            cleaned = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Remove trailing comma if present (but preserve the dependency string)
                    if line.endswith(','):
                        line = line[:-1].strip()
                    # Ensure we have a valid dependency string
                    if line:
                        cleaned.append(line)
            
            return cleaned
        
        # Extract dependencies
        print(f"[DEBUG] Extracting dependencies from original content...", file=sys.stderr)
        deps_lines = extract_array_content(original_content, 'dependencies')
        dev_deps_lines = extract_array_content(original_content, 'dev')
        
        print(f"[DEBUG] Extracted {len(deps_lines)} dependencies", file=sys.stderr)
        print(f"[DEBUG] Raw extracted dependencies: {deps_lines}", file=sys.stderr)
        print(f"[DEBUG] Extracted {len(dev_deps_lines)} dev dependencies", file=sys.stderr)
        print(f"[DEBUG] Raw extracted dev dependencies: {dev_deps_lines}", file=sys.stderr)
        
        # Verify we got all dependencies (debug)
        if len(deps_lines) < 9:  # Should have at least 9-10 dependencies
            print(f"Warning: Only found {len(deps_lines)} dependencies, expected 10", file=sys.stderr)
            print(f"Found: {deps_lines}", file=sys.stderr)
        
        # Validate extracted dependencies - check for common issues
        for i, dep in enumerate(deps_lines):
            dep_stripped = dep.strip()
            # Remove quotes if present for validation
            dep_no_quotes = dep_stripped
            if dep_stripped.startswith('"') and dep_stripped.endswith('"'):
                dep_no_quotes = dep_stripped[1:-1]
            
            # Check for uvicorn specifically - must have full string with version
            if 'uvicorn' in dep_no_quotes:
                if '>=0.38.0' not in dep_no_quotes:
                    print(f"Error: uvicorn dependency missing version: {repr(dep_stripped)}", file=sys.stderr)
                    # Try to fix - add version if missing
                    if 'uvicorn[standard' in dep_no_quotes:
                        fixed = f'uvicorn[standard]>=0.38.0'
                        deps_lines[i] = fixed
                        print(f"  Fixed to: {repr(fixed)}", file=sys.stderr)
            # Check if any dependency is missing closing quote (only if it starts with quote)
            if dep_stripped.startswith('"') and not dep_stripped.endswith('"'):
                print(f"Error: Dependency {i+1} missing closing quote: {repr(dep_stripped)}", file=sys.stderr)
        
        # Fallback: If extraction failed or uvicorn is broken, use known good dependencies
        # These are stored without quotes - formatting code will add them
        KNOWN_DEPS = [
            'asyncpg>=0.30.0',
            'authlib>=1.6.5',
            'fastapi>=0.121.0',
            'greenlet>=3.2.4',
            'httpx>=0.28.1',
            'pydantic>=2.0.0',
            'pydantic-settings>=2.11.0',
            'sqlalchemy>=2.0.44',
            'uvicorn[standard]>=0.38.0',
            'workos>=5.0.0',
        ]
        KNOWN_DEV_DEPS = [
            'alembic>=1.17.1',
            'psycopg2-binary>=2.9.11',
        ]
        
        # Check if we need to use fallback
        use_fallback = False
        if len(deps_lines) < 9:
            use_fallback = True
            print("Warning: Using fallback dependencies due to extraction issues", file=sys.stderr)
        else:
            # Check if uvicorn is broken
            uvicorn_dep = next((d for d in deps_lines if 'uvicorn' in d), None)
            if uvicorn_dep:
                uvicorn_stripped = uvicorn_dep.strip()
                # Remove quotes if present for validation
                if uvicorn_stripped.startswith('"') and uvicorn_stripped.endswith('"'):
                    uvicorn_stripped = uvicorn_stripped[1:-1]
                # Check if version is missing or dependency is truncated
                if '>=0.38.0' not in uvicorn_stripped or not uvicorn_stripped:
                    use_fallback = True
                    print("Warning: Using fallback dependencies due to broken uvicorn extraction", file=sys.stderr)
            # Also check if any dependency is malformed (empty or contains invalid characters)
            for dep in deps_lines:
                dep_stripped = dep.strip()
                # Remove quotes if present for validation
                if dep_stripped.startswith('"') and dep_stripped.endswith('"'):
                    dep_stripped = dep_stripped[1:-1]
                # Check if dependency is empty or doesn't look like a valid package spec
                if not dep_stripped or ' ' in dep_stripped:
                    use_fallback = True
                    print(f"Warning: Using fallback due to malformed dependency: {repr(dep_stripped[:50])}", file=sys.stderr)
                    break
        
        if use_fallback:
            print(f"[DEBUG] Using fallback dependencies", file=sys.stderr)
            deps_lines = KNOWN_DEPS
            dev_deps_lines = KNOWN_DEV_DEPS
        else:
            print(f"[DEBUG] Using extracted dependencies (not fallback)", file=sys.stderr)
        
        print(f"[DEBUG] Final deps_lines before formatting: {deps_lines}", file=sys.stderr)
        print(f"[DEBUG] Final dev_deps_lines before formatting: {dev_deps_lines}", file=sys.stderr)
        
        # Format dependencies with proper indentation
        # Ensure each dependency is properly quoted and has a trailing comma
        # Reference: https://toml.io/en/v1.0.0#array
        print(f"[DEBUG] Formatting dependencies...", file=sys.stderr)
        formatted_deps = []
        for i, dep in enumerate(deps_lines):
            original_dep = dep
            dep = dep.strip()
            print(f"[DEBUG]   Processing dep {i+1}: original={repr(original_dep)}, after strip={repr(dep)}", file=sys.stderr)
            # Remove any existing trailing comma (we'll add it back consistently)
            if dep.endswith(','):
                dep = dep[:-1].strip()
                print(f"[DEBUG]     Removed trailing comma, now: {repr(dep)}", file=sys.stderr)
            # Remove any existing quotes to avoid double-quoting
            if dep.startswith('"') and dep.endswith('"'):
                dep = dep[1:-1]  # Remove outer quotes
                print(f"[DEBUG]     Removed quotes, now: {repr(dep)}", file=sys.stderr)
            # Ensure it's properly quoted
            dep = f'"{dep}"'
            # Always add trailing comma for proper TOML array formatting
            formatted_line = f'    {dep},'
            formatted_deps.append(formatted_line)
            print(f"[DEBUG]     Final formatted line: {repr(formatted_line)}", file=sys.stderr)
        
        # Join with newlines to ensure each dependency is on its own line
        deps_formatted = '\n'.join(formatted_deps)
        print(f"[DEBUG] Final deps_formatted (joined):\n{deps_formatted}", file=sys.stderr)
        print(f"[DEBUG] deps_formatted contains {deps_formatted.count(chr(10))} newlines", file=sys.stderr)
        
        # Format dev dependencies similarly
        print(f"[DEBUG] Formatting dev dependencies...", file=sys.stderr)
        formatted_dev_deps = []
        for i, dep in enumerate(dev_deps_lines):
            original_dep = dep
            dep = dep.strip()
            print(f"[DEBUG]   Processing dev dep {i+1}: original={repr(original_dep)}, after strip={repr(dep)}", file=sys.stderr)
            # Remove any existing trailing comma
            if dep.endswith(','):
                dep = dep[:-1].strip()
                print(f"[DEBUG]     Removed trailing comma, now: {repr(dep)}", file=sys.stderr)
            # Remove any existing quotes to avoid double-quoting
            if dep.startswith('"') and dep.endswith('"'):
                dep = dep[1:-1]  # Remove outer quotes
                print(f"[DEBUG]     Removed quotes, now: {repr(dep)}", file=sys.stderr)
            # Ensure it's properly quoted
            dep = f'"{dep}"'
            # Always add trailing comma for proper TOML array formatting
            formatted_line = f'    {dep},'
            formatted_dev_deps.append(formatted_line)
            print(f"[DEBUG]     Final formatted line: {repr(formatted_line)}", file=sys.stderr)
        
        # Join with newlines to ensure each dependency is on its own line
        dev_deps_formatted = '\n'.join(formatted_dev_deps)
        print(f"[DEBUG] Final dev_deps_formatted (joined):\n{dev_deps_formatted}", file=sys.stderr)
        print(f"[DEBUG] dev_deps_formatted contains {dev_deps_formatted.count(chr(10))} newlines", file=sys.stderr)
        
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
{deps_formatted}
]

# Development dependencies
[project.optional-dependencies]
dev = [
{dev_deps_formatted}
]
"""
        print(f"[DEBUG] Final clean_content length: {len(clean_content)} chars", file=sys.stderr)
        print(f"[DEBUG] Final clean_content:\n{clean_content}", file=sys.stderr)
        print(f"[DEBUG] Writing to: {pyproject_path}", file=sys.stderr)
        pyproject_path.write_text(clean_content)
        print(f"[DEBUG] File written successfully", file=sys.stderr)
        
        # Verify what was actually written
        try:
            written_content = pyproject_path.read_text(encoding='utf-8')
            print(f"[DEBUG] Verification: Read back {len(written_content)} chars", file=sys.stderr)
            deps_section = written_content.split('dependencies = [')[1].split(']')[0] if 'dependencies = [' in written_content else "NOT FOUND"
            print(f"[DEBUG] Verification: dependencies section from written file:\n{deps_section}", file=sys.stderr)
        except Exception as e:
            print(f"[DEBUG] Verification failed: {e}", file=sys.stderr)
    
    print(f"✓ Created new FastAPI project: {dest_dir}")


def find_package_root() -> Path:
    """
    Find the root directory containing template files.
    
    When installed as a package, template files are accessed via importlib.resources.
    In development mode, they're in the project root.
    """
    try:
        # First, try development mode (current file's parent's parent)
        package_file = Path(__file__).resolve()
        dev_root = package_file.parent.parent
        
        # Check if we're in development mode
        if (dev_root / "app").exists() and (dev_root / "alembic").exists():
            return dev_root
        
        # If installed as a package, templates are in fastapi_auth_starter/templates/
        # Check the package directory for templates
        package_dir = Path(__file__).parent  # fastapi_auth_starter/
        templates_dir = package_dir / "templates"
        
        if templates_dir.exists() and (templates_dir / "app").exists() and (templates_dir / "alembic").exists():
            return templates_dir
        
        
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
        project_name: Name of the new project, or '.' to use current directory
        target_dir: Target directory (defaults to current directory/project_name, or current directory if project_name is '.')
    """
    # Handle '.' as special case to initialize in current directory
    if project_name == ".":
        target_dir = Path.cwd()
        # Use current directory name as project name, or a default
        project_name = Path.cwd().name or "fastapi-project"
    elif target_dir is None:
        target_dir = Path.cwd() / project_name
    
    # Check if target directory already exists and is not empty (unless it's current dir with '.')
    if target_dir.exists() and target_dir != Path.cwd():
        # Check if directory is empty
        try:
            if any(target_dir.iterdir()):
                print(f"Error: Directory {target_dir} already exists and is not empty!")
                sys.exit(1)
        except PermissionError:
            print(f"Error: Permission denied accessing {target_dir}")
            sys.exit(1)
    
    # If initializing in current directory, check if it's empty
    if target_dir == Path.cwd():
        try:
            # Check for existing project files
            existing_files = list(Path.cwd().iterdir())
            # Filter out common non-project files
            ignored = {'.git', '.venv', '__pycache__', '.DS_Store', '.idea', '.vscode'}
            project_files = [f for f in existing_files if f.name not in ignored]
            if project_files:
                print(f"Warning: Current directory is not empty. Existing files will be preserved.")
                print(f"Project files will be added to: {target_dir}")
                response = input("Continue? (y/N): ")
                if response.lower() != 'y':
                    print("Aborted.")
                    sys.exit(0)
        except PermissionError:
            print(f"Error: Permission denied accessing current directory")
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
    if target_dir != Path.cwd():
        print(f"  1. cd {target_dir}")
        print(f"  2. Copy .env.example to .env and configure your settings:")
        print(f"     cp .env.example .env")
        print(f"     # Then edit .env with your actual values")
    else:
        print(f"  1. Copy .env.example to .env and configure your settings:")
        print(f"     cp .env.example .env")
        print(f"     # Then edit .env with your actual values")
    print(f"  2. Install dependencies (including dev dependencies for Alembic):")
    print(f"     uv sync --extra dev")
    print(f"     # This installs both runtime and dev dependencies")
    print(f"  3. (Optional) Run example migrations to create users/tasks tables:")
    print(f"     uv run alembic upgrade head")
    print(f"     # Note: These are example migrations. Delete alembic/versions/ if starting fresh.")
    print(f"  4. Start the development server:")
    print(f"     uv run uvicorn app.main:app --reload")


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
  fastapi-auth-starter init .              # Initialize in current directory
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a new FastAPI project")
    init_parser.add_argument(
        "project_name",
        help="Name of the new project, or '.' to initialize in current directory"
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

