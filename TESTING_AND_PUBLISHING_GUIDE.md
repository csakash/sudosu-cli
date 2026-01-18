# Sudosu Testing and Publishing Guide

## ✅ Local Testing Complete!

We've successfully built and tested version **0.1.4** of sudosu locally.

### What We Did:

1. **Updated Version Numbers**
   - Updated `pyproject.toml` to version 0.1.4
   - Updated `sudosu/__init__.py` to version 0.1.4
   - Updated `CHANGELOG.md` with version 0.1.4

2. **Built Distribution Packages**
   - Created source distribution (`.tar.gz`)
   - Created wheel distribution (`.whl`)
   - Both files are in `dist/` directory

3. **Local Testing**
   - Created fresh virtual environment
   - Installed the wheel package
   - Verified version: ✅ 0.1.4
   - Verified CLI help command: ✅ Working
   - Verified entry point: ✅ `sudosu` command available

## 📦 Distribution Files Ready

```
dist/
├── sudosu-0.1.4-py3-none-any.whl  # Wheel package (preferred)
└── sudosu-0.1.4.tar.gz             # Source distribution
```

---

## 🚀 Publishing to PyPI

### Prerequisites

1. **Install Twine** (if not already installed)
   ```bash
   pip3 install twine
   ```

2. **Get PyPI API Token**
   - Go to https://pypi.org/manage/account/
   - Navigate to "API tokens" section
   - Create a new API token with scope for "Entire account" or just the "sudosu" project
   - **IMPORTANT**: Copy and save the token immediately (you won't see it again!)

### Option 1: Test on Test PyPI First (RECOMMENDED)

This is recommended for first-time publishing or major changes.

1. **Get Test PyPI Token**
   - Go to https://test.pypi.org/manage/account/
   - Create API token

2. **Upload to Test PyPI**
   ```bash
   cd /Users/akashmunshi/Projects/langgraph-skills/sudosu
   
   python3 -m twine upload --repository testpypi dist/sudosu-0.1.4*
   ```
   
   When prompted:
   - Username: `__token__`
   - Password: Your Test PyPI token (starts with `pypi-`)

3. **Test Installation from Test PyPI**
   ```bash
   # Create test environment
   python3 -m venv test-testpypi
   source test-testpypi/bin/activate
   
   # Install from Test PyPI
   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ sudosu
   
   # Test it
   sudosu --version
   sudosu --help
   
   # Clean up
   deactivate
   rm -rf test-testpypi
   ```

### Option 2: Publish Directly to Production PyPI

Use this if you've already tested or are confident with the release.

1. **Upload to PyPI**
   ```bash
   cd /Users/akashmunshi/Projects/langgraph-skills/sudosu
   
   python3 -m twine upload dist/sudosu-0.1.4*
   ```
   
   When prompted:
   - Username: `__token__`
   - Password: Your PyPI token (starts with `pypi-`)

2. **Verify Upload**
   - Visit https://pypi.org/project/sudosu/
   - Check that version 0.1.4 appears

3. **Test Installation**
   ```bash
   # Create fresh test environment
   python3 -m venv test-pypi-install
   source test-pypi-install/bin/activate
   
   # Install from PyPI
   pip install sudosu
   
   # Test it
   sudosu --version  # Should show 0.1.4
   sudosu --help
   
   # Clean up
   deactivate
   rm -rf test-pypi-install
   ```

---

## 🔐 Using API Tokens (Recommended Method)

Instead of entering credentials every time, you can store them in `~/.pypirc`:

```bash
cat > ~/.pypirc << 'EOF'
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
EOF

chmod 600 ~/.pypirc  # Secure the file
```

Then you can upload without being prompted:

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/sudosu-0.1.4*

# Upload to Production PyPI
twine upload dist/sudosu-0.1.4*
```

---

## ✅ Pre-Publishing Checklist

Before publishing, verify:

- [x] Version number updated in `pyproject.toml`
- [x] Version number updated in `sudosu/__init__.py`
- [x] CHANGELOG.md updated with release notes
- [x] All code changes committed to git
- [x] Package builds successfully (`python3 -m build`)
- [x] Package installs locally without errors
- [x] CLI commands work (`--version`, `--help`)
- [ ] PyPI/TestPyPI credentials ready
- [ ] Ready to publish!

---

## 🎯 Post-Publishing Steps

After successfully publishing:

1. **Tag the Release in Git**
   ```bash
   cd /Users/akashmunshi/Projects/langgraph-skills/sudosu
   git tag -a v0.1.4 -m "Release version 0.1.4"
   git push origin v0.1.4
   ```

2. **Create GitHub Release** (if using GitHub)
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Select tag `v0.1.4`
   - Copy release notes from CHANGELOG.md
   - Publish release

3. **Verify Installation for Users**
   ```bash
   pip install --upgrade sudosu
   ```

4. **Update Documentation**
   - Update README badges if needed
   - Announce release on social media/blog
   - Update any installation documentation

---

## 🐛 Troubleshooting

### Error: "File already exists"
This means version 0.1.4 is already published. You'll need to:
1. Bump version to 0.1.5
2. Update files and rebuild
3. Try uploading again

### Error: "Invalid credentials"
- Make sure username is `__token__` (including double underscores)
- Verify your API token is correct and not expired
- Check you're using the right token (Test PyPI vs Production PyPI)

### Error: "Package not found" after upload
- Wait a few minutes for PyPI CDN to update
- Clear pip cache: `pip cache purge`
- Try installing with `--no-cache-dir` flag

---

## 📊 Monitoring Your Package

After publishing:

- **PyPI Stats**: https://pypi.org/project/sudosu/
- **Download Stats**: https://pepy.tech/project/sudosu
- **GitHub Stars** (if applicable)

---

## 🔄 Future Releases

For subsequent releases:

1. Make your code changes
2. Update version numbers (bump patch, minor, or major version)
3. Update CHANGELOG.md
4. Build: `rm -rf dist/ build/ *.egg-info && python3 -m build`
5. Test locally
6. Upload to PyPI: `twine upload dist/*`
7. Tag and create GitHub release

---

## 📝 Quick Command Reference

```bash
# Build package
python3 -m build

# Check package contents
twine check dist/*

# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Upload to Production PyPI
twine upload dist/*

# Install and test
pip install sudosu
sudosu --version
```

---

## 🎉 Ready to Publish!

Your package is tested and ready. When you're ready to publish, just run:

```bash
# Install twine if needed
pip3 install twine

# Upload to PyPI (you'll be prompted for credentials)
cd /Users/akashmunshi/Projects/langgraph-skills/sudosu
python3 -m twine upload dist/sudosu-0.1.4*
```

Good luck with your release! 🚀
