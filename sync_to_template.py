#!/usr/bin/env python3
"""
Sync script to copy changes from root project to template.

Usage:
    python sync_to_template.py              # Dry run (shows what would change)
    python sync_to_template.py --apply      # Actually copy files
    python sync_to_template.py --models     # Only sync models
    python sync_to_template.py --all        # Sync everything (models, routes, schemas, services)
"""
import argparse
import shutil
import sys
from pathlib import Path
from typing import List, Set

# Paths
ROOT = Path(__file__).parent
TEMPLATE = ROOT / "fastapi_auth_starter" / "templates"

# File mappings: (root_path, template_path, description)
FILE_MAPPINGS = [
    # Models
    ("app/models", "app/models", "models"),
    # Routes
    ("app/api/v1/routes", "app/api/v1/routes", "routes"),
    # API router
    ("app/api/v1/api.py", "app/api/v1/api.py", "api router"),
    # Schemas
    ("app/api/v1/schemas", "app/api/v1/schemas", "schemas"),
    # Services
    ("app/services", "app/services", "services"),
    # Core files
    ("app/core", "app/core", "core"),
    # Alembic
    ("alembic/env.py", "alembic/env.py", "alembic env"),
    ("alembic.ini", "alembic.ini", "alembic config"),
    # Main app
    ("app/main.py", "app/main.py", "main app"),
    # Other config files
    ("README.md", "README.md", "README"),
    (".env.example", ".env.example", "env example"),
]


def get_python_files(directory: Path) -> List[Path]:
    """Get all Python files in a directory (excluding __pycache__)."""
    if not directory.exists():
        return []
    return [
        f for f in directory.rglob("*.py")
        if "__pycache__" not in str(f) and f.is_file()
    ]


def get_model_names(root_models_dir: Path) -> Set[str]:
    """Extract model class names from model files."""
    models = set()
    if not root_models_dir.exists():
        return models
    
    for model_file in root_models_dir.glob("*.py"):
        if model_file.name == "__init__.py":
            continue
        try:
            content = model_file.read_text()
            # Look for class definitions that inherit from Base
            for line in content.split("\n"):
                if "class " in line and "Base" in content:
                    class_name = line.split("class ")[1].split("(")[0].strip()
                    if class_name and class_name[0].isupper():
                        models.add(class_name)
        except Exception:
            pass
    return models


def update_alembic_env(root_env: Path, template_env: Path, model_names: Set[str], dry_run: bool):
    """Update alembic/env.py to import all models."""
    if not root_env.exists():
        print(f"  ⚠️  Root {root_env} not found, skipping")
        return
    
    content = root_env.read_text()
    
    # Find the import line
    import_line = None
    for line in content.split("\n"):
        if "from app.models import" in line or "from app.models import" in line:
            import_line = line
            break
    
    if import_line:
        # Extract existing imports
        if "from app.models import" in import_line:
            # Parse: from app.models import Task, User
            imports_part = import_line.split("import")[1].strip()
            existing = [m.strip() for m in imports_part.split(",")]
            existing = [m for m in existing if m]
        else:
            existing = []
        
        # Add new models
        all_models = sorted(set(existing + list(model_names)))
        new_import = f"from app.models import {', '.join(all_models)}  # Import all models here so Alembic can detect them"
        
        # Replace the line
        new_content = content.replace(import_line, new_import)
        
        if new_content != content:
            if dry_run:
                print(f"  📝 Would update {template_env.name}:")
                print(f"     Old: {import_line}")
                print(f"     New: {new_import}")
            else:
                template_env.write_text(new_content)
                print(f"  ✅ Updated {template_env.name}")
        else:
            print(f"  ✓  {template_env.name} already up to date")
    else:
        print(f"  ⚠️  Could not find model import in {root_env}")


def sync_directory(root_dir: Path, template_dir: Path, description: str, dry_run: bool):
    """Sync all files from root directory to template directory."""
    if not root_dir.exists():
        print(f"  ⚠️  {root_dir} does not exist, skipping")
        return
    
    template_dir.mkdir(parents=True, exist_ok=True)
    
    # Get all Python files
    files = get_python_files(root_dir)
    
    if not files:
        print(f"  ℹ️  No files to sync in {description}")
        return
    
    copied = 0
    for file_path in files:
        # Calculate relative path from root_dir
        rel_path = file_path.relative_to(root_dir)
        template_file = template_dir / rel_path
        
        # Create parent directories
        template_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Check if file exists and is different
        if template_file.exists():
            if file_path.read_bytes() == template_file.read_bytes():
                continue  # Files are identical, skip
            else:
                action = "update"
        else:
            action = "create"
        
        if dry_run:
            print(f"  📝 Would {action}: {rel_path}")
        else:
            shutil.copy2(file_path, template_file)
            print(f"  ✅ {action.capitalize()}d: {rel_path}")
        
        copied += 1
    
    if copied == 0:
        print(f"  ✓  {description} already in sync")
    elif not dry_run:
        print(f"  ✅ Synced {copied} file(s) in {description}")


def sync_single_file(root_file: Path, template_file: Path, description: str, dry_run: bool):
    """Sync a single file."""
    if not root_file.exists():
        print(f"  ⚠️  {root_file} does not exist, skipping")
        return
    
    template_file.parent.mkdir(parents=True, exist_ok=True)
    
    if template_file.exists():
        if root_file.read_bytes() == template_file.read_bytes():
            print(f"  ✓  {description} already in sync")
            return
        action = "update"
    else:
        action = "create"
    
    if dry_run:
        print(f"  📝 Would {action}: {description}")
    else:
        shutil.copy2(root_file, template_file)
        print(f"  ✅ {action.capitalize()}d: {description}")


def sync_models_init(root_init: Path, template_init: Path, model_names: Set[str], dry_run: bool):
    """Update models __init__.py to include all models."""
    if not root_init.exists():
        print(f"  ⚠️  {root_init} not found, skipping")
        return
    
    content = root_init.read_text()
    
    # Extract existing imports and __all__
    lines = content.split("\n")
    import_lines = []
    all_line = None
    all_start_idx = None
    
    for i, line in enumerate(lines):
        if "from app.models." in line and "import" in line:
            import_lines.append((i, line))
        elif "__all__" in line:
            all_line = line
            all_start_idx = i
            break
    
    # Build new imports and __all__
    new_imports = []
    for model_name in sorted(model_names):
        model_file = model_name.lower()
        import_line = f"from app.models.{model_file} import {model_name}"
        if not any(import_line in line for _, line in import_lines):
            new_imports.append(import_line)
    
    # Update content
    if new_imports or all_line:
        # Add new imports after existing ones
        if import_lines:
            last_import_idx = import_lines[-1][0]
            for new_import in new_imports:
                lines.insert(last_import_idx + 1, new_import)
                last_import_idx += 1
        else:
            # No existing imports, add after Base import
            base_idx = next((i for i, line in enumerate(lines) if "from app.core.database import Base" in line), 0)
            for new_import in new_imports:
                lines.insert(base_idx + 1, new_import)
        
        # Update __all__
        if all_line:
            all_models = sorted(model_names | {"Base"})
            new_all = f'__all__ = {all_models}'
            if all_start_idx is not None:
                lines[all_start_idx] = new_all
        
        new_content = "\n".join(lines)
        
        if new_content != content:
            if dry_run:
                print(f"  📝 Would update {template_init.name}")
                if new_imports:
                    print(f"     Add imports: {', '.join(new_imports)}")
            else:
                template_init.write_text(new_content)
                print(f"  ✅ Updated {template_init.name}")
        else:
            print(f"  ✓  {template_init.name} already up to date")
    else:
        # Just copy as-is
        sync_single_file(root_init, template_init, "models __init__", dry_run)


def main():
    parser = argparse.ArgumentParser(description="Sync files from root project to template")
    parser.add_argument("--apply", action="store_true", help="Actually copy files (default is dry-run)")
    parser.add_argument("--models", action="store_true", help="Only sync models")
    parser.add_argument("--all", action="store_true", help="Sync everything")
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    print(f"{'🔍 DRY RUN' if dry_run else '🚀 APPLYING CHANGES'}")
    print(f"Root: {ROOT}")
    print(f"Template: {TEMPLATE}\n")
    
    # Get model names from root project
    root_models_dir = ROOT / "app" / "models"
    model_names = get_model_names(root_models_dir)
    print(f"📦 Found models: {', '.join(sorted(model_names)) if model_names else 'None'}\n")
    
    # Determine what to sync
    if args.models:
        mappings = [m for m in FILE_MAPPINGS if "models" in m[2] or "alembic" in m[2]]
    elif args.all:
        mappings = FILE_MAPPINGS
    else:
        # Default: sync models and alembic
        mappings = [m for m in FILE_MAPPINGS if "models" in m[2] or "alembic" in m[2]]
    
    # Sync files
    for root_path_str, template_path_str, description in mappings:
        root_path = ROOT / root_path_str
        template_path = TEMPLATE / template_path_str
        
        print(f"\n📁 {description.upper()}")
        
        if root_path.is_dir():
            sync_directory(root_path, template_path, description, dry_run)
        elif root_path.is_file():
            sync_single_file(root_path, template_path, description, dry_run)
        else:
            print(f"  ⚠️  {root_path} not found")
    
    # Update models __init__.py
    if "models" in [m[2] for m in mappings]:
        print(f"\n📁 MODELS __INIT__")
        root_init = ROOT / "app" / "models" / "__init__.py"
        template_init = TEMPLATE / "app" / "models" / "__init__.py"
        sync_models_init(root_init, template_init, model_names, dry_run)
    
    # Update alembic/env.py
    if "alembic" in [m[2] for m in mappings]:
        print(f"\n📁 ALEMBIC ENV")
        root_env = ROOT / "alembic" / "env.py"
        template_env = TEMPLATE / "alembic" / "env.py"
        update_alembic_env(root_env, template_env, model_names, dry_run)
    
    print(f"\n{'✅ Dry run complete. Use --apply to actually sync files.' if dry_run else '✅ Sync complete!'}")


if __name__ == "__main__":
    main()

