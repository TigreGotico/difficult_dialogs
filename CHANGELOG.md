# Changelog

All notable changes to this project will be documented in this file.

## [0.4.0] - 2026-03-30

### Changed
- **BREAKING**: Complete ground-up rewrite for Python 3.10+
- **BREAKING**: New API with dataclasses and type hints
- **BREAKING**: Policy system now uses `asyncio` instead of threading
- **BREAKING**: `BasePolicy` is now an abstract base class
- Renamed package to `difficult-dialogs` (PyPI naming convention)

### Added
- `@dataclass` decorators for `Statement`, `Premise`, `Argument`
- Full type hints with mypy strict mode compliance
- `SilentPolicy` for one-way presentations
- Async dialog support with `run_async()` and `stream()`
- Sync generator-based dialog with `run_sync()`
- Support for both new (subdirectory) and legacy (flat) argument formats
- Five Ws support: what, why, how, when, where explanations
- Method chaining for premise/argument builders
- `to_dict()` / `from_dict()` roundtrip serialization
- GitHub Actions CI workflow
- Comprehensive unit tests (58 tests)

### Removed
- Threading-based async model
- Legacy `run_async()` / `stop()` / `submit_input()` pattern
- Unused exception classes
- Backwards compatibility with old API

### Fixed
- Type safety issues throughout codebase
- Silent failures when loading invalid argument directories
- Missing validation for premise names

---

## [0.3.0] - 2026-03-30

### Changed
- Added `pyproject.toml` for modern Python packaging
- Added type hints (partial)
- Updated tests

---

## [0.2.0] - Original Release

Initial alpha release with basic argumentation framework.

### Features
- File-based argument definitions
- Policy-based dialog control
- Support statements and sources
- Threading-based async dialog
