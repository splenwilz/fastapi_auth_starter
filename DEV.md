# Development Guide

This guide explains how to develop and maintain the `fastapi-auth-starter` template package.

## Project Structure

```
fastapi_auth_starter/
├── app/                    # Root project (for development/testing)
├── alembic/                # Root Alembic config (for development)
├── fastapi_auth_starter/   # Package source
│   ├── templates/          # Template files (what gets copied to new projects)
│   └── cli.py              # CLI tool for scaffolding
└── sync_to_template.py     # Script to sync changes from root to template
```

## Development Workflow

### 1. Develop in Root Project

Work directly in the root project files:
- `app/models/` - Add new models here
- `app/api/v1/routes/` - Add new routes here
- `app/api/v1/schemas/` - Add new schemas here
- `app/services/` - Add new services here
- `alembic/env.py` - Update model imports here

**Example: Adding a Product model**

```bash
# 1. Create the model
app/models/product.py

# 2. Update imports
app/models/__init__.py          # Add: from app.models.product import Product
alembic/env.py                  # Add: Product to model imports

# 3. Create related files
app/api/v1/schemas/product.py
app/api/v1/routes/product.py
app/services/product.py
app/api/v1/api.py              # Add product router

# 4. Test locally
uv run alembic revision --autogenerate -m "Add product model"
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

### 2. Sync to Template

Once your changes are tested and working, sync them to the template:

```bash
# Dry run (see what would change)
uv run python sync_to_template.py

# Sync only models
uv run python sync_to_template.py --models --apply

# Sync everything (models, routes, schemas, services, etc.)
uv run python sync_to_template.py --all --apply
```

The sync script will:
- ✅ Copy new files to template
- ✅ Update `__init__.py` files automatically
- ✅ Update `alembic/env.py` with new models
- ✅ Show what changed

### 3. Test the Template

Generate a test project to verify the template works:

```bash
# Create a test project
fastapi-auth-starter init test-project
cd test-project

# Verify your new features are included
ls app/models/
cat alembic/env.py  # Should include your new models

# Test it works
uv sync --extra dev
uv run alembic revision --autogenerate -m "Initial migration"
```

### 4. Publish

Once everything is tested:

```bash
# Bump version in pyproject.toml and __init__.py
# Then publish
uv build
uv publish
```

## Sync Script Usage

The `sync_to_template.py` script helps you copy changes from the root project to the template.

### Commands

```bash
# Dry run (default) - shows what would change
uv run python sync_to_template.py

# Actually sync files
uv run python sync_to_template.py --apply

# Only sync models and Alembic config
uv run python sync_to_template.py --models --apply

# Sync everything (models, routes, schemas, services, core, etc.)
uv run python sync_to_template.py --all --apply
```

### What Gets Synced

By default (without `--all`):
- ✅ Models (`app/models/`)
- ✅ Alembic config (`alembic/env.py`, `alembic.ini`)

With `--all` flag:
- ✅ Models (`app/models/`)
- ✅ Routes (`app/api/v1/routes/`)
- ✅ API Router (`app/api/v1/api.py`)
- ✅ Schemas (`app/api/v1/schemas/`)
- ✅ Services (`app/services/`)
- ✅ Core (`app/core/`)
- ✅ Alembic config
- ✅ Main app (`app/main.py`)
- ✅ README and config files

### Automatic Updates

The script automatically:
- Updates `app/models/__init__.py` with new model imports
- Updates `alembic/env.py` with new model imports
- Detects model classes from your code

## Adding a New Model

Complete workflow example:

```bash
# 1. Create model file
cat > app/models/product.py << 'EOF'
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
EOF

# 2. Update root project imports
# Edit app/models/__init__.py - add: from app.models.product import Product
# Edit alembic/env.py - add: Product to imports

# 3. Test locally
uv run alembic revision --autogenerate -m "Add product"
uv run alembic upgrade head

# 4. Sync to template
uv run python sync_to_template.py --all --apply

# 5. Test template
fastapi-auth-starter init test-product
cd test-product
# Verify product.py exists and works
```

## Important Notes

1. **Always test in root project first** - Make sure everything works before syncing
2. **Use dry-run first** - Check what will change before applying
3. **Keep templates simple** - The template should be the "clean" version users get
4. **Version control** - Commit root changes and template changes separately for clarity

## Troubleshooting

### Sync script not detecting models

Make sure your model class:
- Inherits from `Base`
- Is in a `.py` file (not `__init__.py`)
- Has `class ModelName(Base):` format

### Import errors after sync

Check that:
- `app/models/__init__.py` has the import
- `alembic/env.py` has the model in imports
- Model file exists in template directory

### Files not syncing

The script only syncs files listed in `FILE_MAPPINGS`. If you need to sync other files, add them to the script or copy manually.

## Contributing

When adding features:
1. Develop in root project
2. Test thoroughly
3. Sync to template
4. Test template generation
5. Update version and publish

