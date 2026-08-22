# Contributing to Virtual Fence

First off, thank you for considering contributing to Virtual Fence!

## Development Setup

1. Fork and clone the repository.
2. Create a Python virtual environment and install development dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```
3. Install Node dependencies:
   ```bash
   cd frontend
   npm install
   ```
4. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Development Workflow

1. Create a feature branch: `git checkout -b feature/my-new-feature`
2. Make your changes.
3. Run the tests to ensure nothing is broken:
   ```bash
   pytest tests/
   ```
4. Ensure code formatting and typing passes:
   ```bash
   ruff check backend/
   ruff format backend/
   mypy backend/
   ```
5. Commit your changes. Pre-commit hooks will run automatically.
6. Push to the branch and open a Pull Request.

## Code Style

- **Python**: We use `ruff` for linting and formatting. Line length is 100 characters. We use type hints extensively, checked by `mypy`.
- **TypeScript**: We use standard `eslint` and `prettier` (via Next.js defaults).

## Testing

All new features or bug fixes should be accompanied by tests. We use `pytest` for the backend.
