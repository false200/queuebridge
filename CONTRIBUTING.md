# Contributing to queuebridge

Thanks for helping improve queuebridge!

## Quick start

1. Fork the repo and create a branch from `main`
2. Install dev dependencies: `pip install -e ".[all,dev,docs]"`
3. Make your changes
4. Run checks:

   ```bash
   ruff check .
   mypy src
   pytest
   ```

5. Open a pull request using the PR template

## What to contribute

* Bug fixes
* Documentation improvements ([docs](https://queuebridge.readthedocs.io))
* Tests for edge cases
* Backend adapter improvements (Celery, Dramatiq, Arq)

## Pull requests

* Keep PRs focused (one concern per PR)
* Add tests when fixing bugs or adding behavior
* Update docs if you change public API
* Follow existing code style (ruff, mypy strict)

## Issues

Before opening a PR for a large change, open an issue to discuss it.

Use the issue templates. Keep it simple: **what the issue is** and **what decision or outcome you want**.

## Labels

Look for [`good first issue`](https://github.com/false200/queuebridge/labels/good%20first%20issue) if you are new to the project.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md).
