# Release Checklist

Use this checklist before publishing to TestPyPI or PyPI.

- Confirm the public protocol contract requires explicit `protocol="adcp"` or `protocol="sdcp"`.
- Run `pytest`.
- Run formatting and linting checks configured for the project.
- Build source and wheel distributions.
- Inspect the generated distribution metadata for package name, version, README rendering, classifiers, and project URLs.
- Publish to TestPyPI first.
- Install from TestPyPI into a clean environment and run the smoke-test import:

```python
from sony_projector_protocol import Projector, discover
```

- Publish to PyPI after the TestPyPI package installs successfully.
