# Publishing to PyPI

This guide walks you through publishing `fastapi-auth-starter` to PyPI so others can install it with `uv add fastapi-auth-starter`.

## Prerequisites

1. **PyPI Account**: Create accounts on both:
   - [PyPI](https://pypi.org/account/register/) - for production releases
   - [TestPyPI](https://test.pypi.org/account/register/) - for testing releases

2. **Choose Publishing Method**:
   - **Option A: Trusted Publishers (Recommended)** - Automated publishing via GitHub Actions (no API tokens needed)
   - **Option B: API Tokens** - Manual publishing using API tokens

### Option A: Trusted Publishers Setup (Recommended)

**Benefits:**
- ✅ No API tokens to manage
- ✅ Automated publishing on releases
- ✅ More secure (uses OpenID Connect)
- ✅ Can be triggered manually or on release

**Setup Steps:**

1. **Create GitHub Actions Environment** (optional but recommended):
   - Go to your repository: `https://github.com/splenwilz/fastapi-auth-starter`
   - Settings → Environments → New environment
   - Name: `pypi`
   - Add any required reviewers (optional)

2. **Configure PyPI Trusted Publisher**:
   - Go to [PyPI Account Settings → Publishing](https://pypi.org/manage/account/publishing/)
   - Click "Add a new pending publisher"
   - Fill in the form:
     - **PyPI Project Name**: `fastapi-auth-starter`
     - **Owner**: `splenwilz`
     - **Repository name**: `fastapi-auth-starter`
     - **Workflow name**: `publish.yml`
     - **Environment name**: `pypi` (optional but recommended)
   - Click "Add"

3. **The workflow is already created** at `.github/workflows/publish.yml`

4. **Publishing**:
   - Create a GitHub release, OR
   - Go to Actions → "Publish to PyPI" → Run workflow

### Option B: API Tokens (Manual Publishing)

**API Tokens**: Generate API tokens for authentication:
- Go to [PyPI Account Settings](https://pypi.org/manage/account/) → API tokens
- Create a token with scope: "Entire account" or "Project: fastapi-auth-starter"
- Save the token securely (format: `pypi-...`)

**Install Publishing Tools**:
```bash
uv pip install build twine
```

## Step-by-Step Publishing Process

### 1. Prepare Your Package

Ensure your `pyproject.toml` has all required metadata:
- ✅ Package name (must be unique on PyPI)
- ✅ Version number
- ✅ Description
- ✅ Author information
- ✅ License
- ✅ Project URLs (GitHub, documentation, etc.)
- ✅ Classifiers (Python version, license, topics)

### 2. Update Version Number

Before publishing, update the version in `pyproject.toml`:

```toml
[project]
version = "0.1.0"  # Use semantic versioning: MAJOR.MINOR.PATCH
```

**Semantic Versioning Guidelines:**
- `0.1.0` → `0.1.1` - Bug fixes (patch)
- `0.1.0` → `0.2.0` - New features, backward compatible (minor)
- `0.1.0` → `1.0.0` - Breaking changes (major)

### 3. Clean Build Artifacts

Remove any previous builds:

```bash
rm -rf dist/ build/ *.egg-info
```

### 4. Build the Package

Build both source distribution (sdist) and wheel:

```bash
# Using uv (recommended)
uv build

# Or using standard build tool
python -m build
```

This creates:
- `dist/fastapi_auth_starter-0.1.0.tar.gz` (source distribution)
- `dist/fastapi_auth_starter-0.1.0-py3-none-any.whl` (wheel)

### 5. Test on TestPyPI (Recommended)

**Upload to TestPyPI first** to verify everything works:

```bash
# Upload to TestPyPI
uv publish --publish-url https://test.pypi.org/legacy/ dist/*

# Or using twine
twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your TestPyPI API token (starts with `pypi-...`)

**Test Installation from TestPyPI:**

```bash
# Create a test environment
mkdir test-install && cd test-install
uv init

# Install from TestPyPI
uv add --index-url https://test.pypi.org/simple/ fastapi-auth-starter

# Test the CLI
fastapi-auth-starter init test-project
```

### 6. Publish to PyPI

Once tested on TestPyPI, publish to production:

```bash
# Using uv (recommended)
uv publish dist/*

# Or using twine
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-...`)

### 7. Verify Publication

Check your package on PyPI:
- https://pypi.org/project/fastapi-auth-starter/

Test installation:

```bash
# In a new project
uv init
uv add fastapi-auth-starter
fastapi-auth-starter init my-project
```

## Using API Tokens (Recommended)

Instead of entering credentials each time, configure tokens:

### Option 1: Environment Variables

```bash
# For PyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here

# For TestPyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-test-token-here
```

### Option 2: Configuration File

Create `~/.pypirc`:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-production-token-here

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-your-test-token-here
```

**Security Note**: Add `~/.pypirc` to `.gitignore` and never commit tokens!

## Automated Publishing Script

Create a `publish.sh` script for convenience:

```bash
#!/bin/bash
set -e

echo "🧹 Cleaning build artifacts..."
rm -rf dist/ build/ *.egg-info

echo "📦 Building package..."
uv build

echo "🧪 Uploading to TestPyPI..."
uv publish --publish-url https://test.pypi.org/legacy/ dist/*

read -p "✅ TestPyPI upload successful! Test installation? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Testing installation from TestPyPI..."
    mkdir -p /tmp/test-fas-install
    cd /tmp/test-fas-install
    uv init
    uv add --index-url https://test.pypi.org/simple/ fastapi-auth-starter
    fastapi-auth-starter --help
    cd -
    rm -rf /tmp/test-fas-install
fi

read -p "🚀 Ready to publish to PyPI? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Publishing to PyPI..."
    uv publish dist/*
    echo "✅ Published! Check https://pypi.org/project/fastapi-auth-starter/"
fi
```

Make it executable:
```bash
chmod +x publish.sh
```

## Updating the Package

For subsequent releases:

1. **Update version** in `pyproject.toml`
2. **Update CHANGELOG.md** (if you have one)
3. **Commit and tag** the release:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.1.1"
   git tag v0.1.1
   git push origin main --tags
   ```
4. **Build and publish**:
   ```bash
   uv build
   uv publish dist/*
   ```

## Troubleshooting

### "Package name already taken"

- The name `fastapi-auth-starter` might be taken
- Choose a different name in `pyproject.toml`
- Or use a namespace like `yourname-fastapi-auth-starter`

### "Invalid version"

- Version must follow PEP 440 (e.g., `0.1.0`, `1.2.3`, `2.0.0a1`)
- Cannot reuse versions (each release needs a new version)

### "Authentication failed"

- Verify your API token is correct
- Ensure you're using `__token__` as username
- Check token hasn't expired or been revoked

### "File already exists"

- Version already published - increment version number
- Or delete the existing release (if you have permissions)

## Best Practices

1. **Always test on TestPyPI first** - Catch issues before production
2. **Use semantic versioning** - Follow MAJOR.MINOR.PATCH
3. **Tag releases in Git** - `git tag v0.1.0 && git push --tags`
4. **Update CHANGELOG** - Document changes between versions
5. **Keep dependencies updated** - Regularly update package dependencies
6. **Monitor package downloads** - Check PyPI statistics

## References

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Documentation](https://pypi.org/help/)
- [Semantic Versioning](https://semver.org/)
- [PEP 440 - Version Identification](https://peps.python.org/pep-0440/)
- [uv publish documentation](https://docs.astral.sh/uv/publishing/)

