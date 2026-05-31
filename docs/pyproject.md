# pyproject.toml

The pyproject.toml is the main configuration file used for the Python project.
It contains configurations for building, linting, testing, and publishing the Python package.

This project uses Flit through the `[build-system]` table in `pyproject.toml`.

Keep runtime metadata, optional test dependencies, pytest settings, coverage settings, and formatter settings in `pyproject.toml` unless a tool requires its own configuration file.
