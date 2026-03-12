# Release Process

## Before Tagging

1. Update `CHANGELOG.md`.
2. Run:

```bash
ruff check aiogram_mcp tests examples
mypy aiogram_mcp
pytest -v
```

3. Verify at least one real bot can start with:

```bash
python examples/basic_bot.py
```

4. Verify one MCP client can connect over the intended transport.
5. Confirm package metadata and README are current.

## Create a Release

1. Bump the version in `pyproject.toml`.
2. Commit the release changes.
3. Create and push a tag:

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

4. Confirm GitHub Actions completed successfully.
5. Publish GitHub release notes from the changelog.

## After Release

1. Smoke test the published package in a clean virtual environment.
2. Open a follow-up issue for anything deferred from the release.
