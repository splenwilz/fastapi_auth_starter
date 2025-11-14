#!/bin/bash
# Publishing script for fastapi-auth-starter
# Usage: ./publish.sh [test|prod]

set -e

MODE=${1:-test}

echo "🧹 Cleaning build artifacts..."
rm -rf dist/ build/ *.egg-info

echo "📦 Building package..."
uv build

if [ "$MODE" = "test" ]; then
    echo "🧪 Uploading to TestPyPI..."
    echo "   (Use username: __token__ and your TestPyPI API token)"
    uv publish --publish-url https://test.pypi.org/legacy/ dist/*
    echo ""
    echo "✅ Uploaded to TestPyPI!"
    echo "   Test installation with:"
    echo "   uv add --index-url https://test.pypi.org/simple/ fastapi-auth-starter"
elif [ "$MODE" = "prod" ]; then
    echo "🚀 Publishing to PyPI..."
    echo "   (Use username: __token__ and your PyPI API token)"
    uv publish dist/*
    echo ""
    echo "✅ Published to PyPI!"
    echo "   Check: https://pypi.org/project/fastapi-auth-starter/"
    echo "   Install with: uv add fastapi-auth-starter"
else
    echo "Usage: ./publish.sh [test|prod]"
    exit 1
fi

