# Publishing to PyPI

This document explains how to publish the `ghs` package to PyPI using the GitHub Actions workflow.

## Setup

### Configure Trusted Publishing on PyPI

Before the workflow can publish to PyPI, you need to configure trusted publishing:

1. Go to [PyPI](https://pypi.org/) and log in to your account
2. Navigate to your account settings
3. Go to the "Publishing" tab
4. Click "Add a new pending publisher"
5. Fill in the following details:
   - **PyPI Project Name**: `ghs`
   - **Owner**: `MiguelElGallo`
   - **Repository name**: `ghs`
   - **Workflow name**: `publish-to-pypi.yml`
   - **Environment name**: (leave empty)

This will create a pending publisher that will be activated when you first publish a release.

## Publishing a New Version

To publish a new version to PyPI:

1. Update the version number in `pyproject.toml`:
   ```toml
   [project]
   version = "0.2.0"  # Update this
   ```

2. Commit your changes:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git push
   ```

3. Create and push a new tag:
   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. Create a GitHub Release:
   - Go to the repository on GitHub
   - Click on "Releases" > "Draft a new release"
   - Select the tag you just created (`v0.2.0`)
   - Fill in the release title and description
   - Click "Publish release"

The GitHub Actions workflow will automatically:
- Build the package using `uv build`
- Publish it to PyPI using `uv publish` with trusted publishing

## Manual Triggering

You can also manually trigger the publish workflow:

1. Go to the repository on GitHub
2. Navigate to Actions > "Publish to PyPI"
3. Click "Run workflow"
4. Select the branch and click "Run workflow"

## Testing the Workflow

Before publishing to production PyPI, you can test the workflow by:

1. Setting up a TestPyPI account at https://test.pypi.org/
2. Configuring a separate workflow that publishes to TestPyPI
3. Using `--publish-url https://test.pypi.org/legacy/` in the publish step

## Troubleshooting

### Permission Denied

If you get a permission error, ensure:
- Trusted publishing is correctly configured on PyPI
- The workflow has `id-token: write` permission
- The workflow name matches exactly what you configured on PyPI

### Package Already Exists

PyPI doesn't allow re-uploading the same version. You must:
- Bump the version number in `pyproject.toml`
- Create a new tag and release

## Local Testing

To test building the package locally:

```bash
# Install dependencies
uv sync --extra dev

# Build the package
uv build

# Check the built distributions
ls -la dist/
```

The build artifacts will be in the `dist/` directory (ignored by git).
