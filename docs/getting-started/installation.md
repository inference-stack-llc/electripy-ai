# Installation

## Requirements

- Python 3.11 or higher
- pip, poetry, or uv for package management

## Install from PyPI

```bash
pip install electripy-ai
```

> **Package rename in progress.** Current builds may still be published under the previous package name (`electripy-studio`) during migration. The Python import namespace remains `electripy` in all cases.

## Install from Source

Clone the repository and install in editable mode:

```bash
git clone https://github.com/inference-stack-llc/electripy-ai.git
cd electripy-ai
pip install -e .
```

## Install Development Dependencies

For development work, install with dev dependencies:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest for testing
- ruff for linting
- black for code formatting
- mypy for type checking

## Install Documentation Dependencies

To build the documentation locally:

```bash
pip install -e ".[docs]"
mkdocs serve
```

## Verify Installation

Check that ElectriPy AI is properly installed:

```bash
electripy doctor
```

This command verifies your Python version, dependencies, and configuration.
