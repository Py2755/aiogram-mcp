# Contributing

Thanks for contributing to `aiogram-mcp`.

## Development Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

On Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Local Checks

Run these before opening a pull request:

```bash
ruff check aiogram_mcp tests examples
mypy aiogram_mcp
pytest -v
```

## Pull Request Guidelines

- Keep PRs focused.
- Add or update tests when behavior changes.
- Update `README.md` when public APIs or examples change.
- Update `CHANGELOG.md` for user-visible changes.

## Release Expectations

- Public API changes should be documented.
- New MCP tools must have basic tests and safety notes.
- Examples should be generic and safe to publish.
