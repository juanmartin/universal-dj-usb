# Contributing to Universal DJ USB Playlist Converter

We welcome contributions to the Universal DJ USB Playlist Converter! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Rust toolchain (for rekordcrate dependency)
- Git

### Setting up the development environment

1. Fork the repository
2. Clone your fork:

   ```bash
   git clone https://github.com/your-username/universal-dj-usb.git
   cd universal-dj-usb
   ```

3. Create a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:

   ```bash
   pip install -e ".[dev]"
   ```

5. Install rekordcrate:

   ```bash
   cargo install rekordcrate
   ```

## Development Guidelines

### Code Style

- Follow PEP 8 conventions
- Use type hints for all functions
- Add docstrings to all public functions and classes
- Keep line length under 88 characters
- Use meaningful variable and function names

### Testing

- Write tests for all new functionality
- Ensure all tests pass before submitting a PR
- Aim for high test coverage
- Use pytest for testing

Run tests:

```bash
pytest
```

Run tests with coverage:

```bash
pytest --cov=src/universal_dj_usb --cov-report=html
```

### Code Quality

We use several tools to maintain code quality:

- **Black**: Code formatting
- **flake8**: Linting
- **mypy**: Type checking

Run all checks:

```bash
black src tests
flake8 src tests
mypy src
```

### Pre-commit Hooks

Install pre-commit hooks to ensure code quality:

```bash
pre-commit install
```

## Making Changes

### Branch Naming

Use descriptive branch names:

- `feature/playlist-filtering`
- `bugfix/nml-encoding-issue`
- `docs/api-documentation`

### Commit Messages

Write clear, descriptive commit messages:

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters
- Reference issues and pull requests when applicable

Example:

```
Add support for cue point colors in NML export

- Map Rekordbox cue colors to Traktor hotcue numbers
- Add color conversion utility function
- Update tests for color mapping

Fixes #123
```

### Pull Request Process

1. Ensure your code follows the style guidelines
2. Add or update tests as needed
3. Update documentation if necessary
4. Ensure all tests pass
5. Create a pull request with a clear title and description

## Types of Contributions

### Bug Reports

When filing a bug report, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version)
- Sample files (if applicable)

### Feature Requests

For feature requests, please include:

- Clear description of the feature
- Use case and benefits
- Possible implementation approach
- Any relevant examples or mockups

### Code Contributions

We welcome contributions for:

- Bug fixes
- New features
- Performance improvements
- Documentation improvements
- Test coverage improvements

### Documentation

Help improve our documentation:

- API documentation
- User guides
- Code examples
- README improvements

## Project Structure

```
universal-dj-usb/
├── src/universal_dj_usb/
│   ├── __init__.py
│   ├── models.py          # Data models
│   ├── converter.py       # Main converter class
│   ├── rekordbox_parser.py # Rekordbox database parser
│   ├── nml_generator.py   # Traktor NML generator
│   ├── cli.py            # Command-line interface
│   ├── gui.py            # Graphical user interface
│   └── utils.py          # Utility functions
├── tests/                # Test files
├── docs/                 # Documentation
├── pyproject.toml        # Project configuration
└── README.md
```

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create a release PR
4. Tag the release
5. Build and publish to PyPI

## Community

- Be respectful and inclusive
- Help others learn and contribute
- Follow the [Python Community Code of Conduct](https://www.python.org/psf/conduct/)

## Questions?

If you have questions about contributing, please:

- Open an issue for discussion
- Join our Discord community
- Email us at <contributors@universal-dj-usb.com>

Thank you for contributing to Universal DJ USB Playlist Converter!
