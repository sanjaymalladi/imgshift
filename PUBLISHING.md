# Publishing to PyPI

## Prerequisites

1. **Build tools** installed:
   ```bash
   pip install build twine
   ```

2. **PyPI account** created at [pypi.org](https://pypi.org/account/register/)

3. **API token** generated:
   - Go to [Account Settings → API Tokens](https://pypi.org/manage/account/token/)
   - Create a token for "Entire account" or specific project
   - Save the token securely (starts with `pypi-`)

## Publishing Steps

### 1. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info
# Or on Windows:
rd /s /q dist build src\imgshift.egg-info
```

### 2. Build the Package

```bash
python -m build
```

This creates two files in `dist/`:
- `.tar.gz` (source distribution)
- `.whl` (wheel distribution)

### 3. Check the Build

```bash
twine check dist/*
```

Make sure there are no errors or warnings.

### 4. Test Upload (TestPyPI - Optional but Recommended)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ imgshift
```

### 5. Upload to PyPI

```bash
twine upload dist/*
```

When prompted:
- **Username**: `__token__`
- **Password**: Your API token (including the `pypi-` prefix)

### 6. Verify

```bash
# Install from PyPI
pip install --upgrade imgshift

# Verify version
python -c "import imgshift; print(imgshift.__version__)"
```

## Using API Token (Recommended)

Create `~/.pypirc` file:

```ini
[pypi]
username = __token__
password = pypi-your-api-token-here
```

**Windows**: Create at `C:\Users\YourUsername\.pypirc`

With this file, you can upload without entering credentials:

```bash
twine upload dist/*
```

## Quick Release Checklist

- [ ] Update version in `pyproject.toml` and `src/imgshift/__init__.py`
- [ ] Update `CHANGELOG.md` with changes
- [ ] Update `README.md` if needed
- [ ] Commit and tag release:
  ```bash
  git add .
  git commit -m "Release v0.1.2"
  git tag v0.1.2  
  git push origin main --tags
  ```
- [ ] Clean previous builds: `rm -rf dist/`
- [ ] Build package: `python -m build`
- [ ] Check package: `twine check dist/*`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Verify installation: `pip install --upgrade imgshift`

## For Version 0.1.2

```bash
# Clean
rm -rf dist/ build/ src/imgshift.egg-info

# Build
python -m build

# Check
twine check dist/*

# Upload
twine upload dist/*
```

That's it! Your package is now live on PyPI at `https://pypi.org/project/imgshift/`
