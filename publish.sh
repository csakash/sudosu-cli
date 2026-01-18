#!/bin/bash

# Sudosu PyPI Publishing Script
# This script will help you publish sudosu to PyPI

set -e  # Exit on error

echo "🚀 Sudosu Publishing Script"
echo "============================"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from sudosu package directory"
    exit 1
fi

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo "📦 Installing twine..."
    pip3 install twine
fi

echo "✅ Twine is installed"
echo ""

# Show current version
VERSION=$(grep "^version" pyproject.toml | cut -d'"' -f2)
echo "📌 Current version: $VERSION"
echo ""

# Check if dist files exist
if [ ! -d "dist" ] || [ -z "$(ls -A dist/)" ]; then
    echo "❌ No distribution files found in dist/"
    echo "   Run: python3 -m build"
    exit 1
fi

echo "📦 Distribution files found:"
ls -lh dist/
echo ""

# Check package quality
echo "🔍 Checking package with twine..."
twine check dist/*
echo ""

# Ask user which PyPI to upload to
echo "Where do you want to publish?"
echo "1) Test PyPI (recommended for testing)"
echo "2) Production PyPI (live release)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo ""
        echo "📤 Uploading to Test PyPI..."
        echo "You'll need your Test PyPI API token"
        echo "Get it from: https://test.pypi.org/manage/account/"
        echo ""
        twine upload --repository testpypi dist/sudosu-$VERSION*
        
        echo ""
        echo "✅ Upload complete!"
        echo ""
        echo "Test installation with:"
        echo "  pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sudosu"
        ;;
    2)
        echo ""
        echo "📤 Uploading to Production PyPI..."
        echo "You'll need your PyPI API token"
        echo "Get it from: https://pypi.org/manage/account/"
        echo ""
        read -p "Are you sure? This is a LIVE release! (yes/no): " confirm
        
        if [ "$confirm" = "yes" ]; then
            twine upload dist/sudosu-$VERSION*
            
            echo ""
            echo "✅ Upload complete!"
            echo ""
            echo "🎉 Package is now live at: https://pypi.org/project/sudosu/"
            echo ""
            echo "Test installation with:"
            echo "  pip install --upgrade sudosu"
        else
            echo "❌ Upload cancelled"
            exit 1
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "Don't forget to:"
echo "  1. Tag the release in git: git tag -a v$VERSION -m 'Release $VERSION'"
echo "  2. Push the tag: git push origin v$VERSION"
echo "  3. Create a GitHub release"
