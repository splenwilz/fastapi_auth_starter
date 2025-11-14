# Using FastAPI Auth Starter as a Package

This guide explains how to use this FastAPI starter as a reusable package in your projects.

## Installation Methods

### Option 1: Git Dependency (Recommended for Development)

Install directly from the git repository:

```bash
# In your new project directory
uv init
uv add git+https://github.com/splenwilz/fastapi-auth-starter.git
```

Then copy the files you need manually, or use the CLI tool (see below).

### Option 2: Local Editable Install

Install the package in editable mode for development:

```bash
# In the fastapi-auth-starter directory
uv pip install -e .

# Now you can use the CLI tool
fastapi-auth-starter init my-new-project
```

### Option 3: Install from Local Path

Install from a local directory:

```bash
# In your new project
uv add /path/to/fastapi-auth-starter
```

### Option 4: Install from PyPI (Recommended)

Once published to PyPI, you can install and use it:

```bash
# Install the package (required first step)
uv pip install fastapi-auth-starter

# Now you can use the CLI
fastapi-auth-starter init my-new-project

# Or initialize in current directory
fastapi-auth-starter init .
```

**Quick Start (One-liner):**
```bash
# Install and initialize in one go
uv pip install fastapi-auth-starter && fastapi-auth-starter init .
```

**To publish to PyPI**, see [PUBLISHING.md](./PUBLISHING.md) for detailed instructions.

## Using the CLI Tool

After installation, you can scaffold new projects using the CLI:

```bash
# Initialize a new project in the current directory
fastapi-auth-starter init my-api

# Initialize in a specific directory
fastapi-auth-starter init my-api --dir /path/to/projects
```

The CLI will:
1. Copy all template files (app/, alembic/, config files, etc.)
2. Customize `pyproject.toml` with your project name
3. Create a ready-to-use FastAPI project

## Manual Setup

If you prefer to clone and customize manually:

```bash
# Clone the repository
git clone https://github.com/splenwilz/fastapi-auth-starter.git my-project
cd my-project

# Remove git history (optional)
rm -rf .git

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
uv run alembic upgrade head

# Start the server
uv run uvicorn app.main:app --reload
```

## Package Structure

When installed as a package, the following structure is available:

```text
fastapi_auth_starter/
├── __init__.py
└── cli.py              # CLI tool for scaffolding
```

Template files (app/, alembic/, etc.) are included as package data and can be accessed by the CLI tool.

## Development

To work on the package itself:

```bash
# Install in editable mode
uv pip install -e .

# Test the CLI
fastapi-auth-starter init test-project

# Build the package
uv build

# Install from built wheel
uv pip install dist/fastapi_auth_starter-*.whl
```

## Notes

- The CLI tool automatically detects whether it's running in development mode or as an installed package
- Template files are included in the package distribution
- The package name in `pyproject.toml` is automatically updated when scaffolding new projects

