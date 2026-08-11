# Contributing to ChEBI-N

Thank you for your interest in contributing to ChEBI-N! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. All participants are expected to treat each other with respect and to maintain a harassment-free environment.

## Getting Started

### Prerequisites

- Python 3.12+
- `uv` for dependency management (install from https://docs.astral.sh/uv/)
- Git

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/ontology-tools/chebin.git
   cd chebin
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Run tests to verify setup:
   ```bash
   uv run pytest tests/ -v
   ```

## Development Workflow

### Code Quality Standards

We maintain high standards for code quality across the project. All contributions must:

1. **Pass all tests**: Run `uv run pytest tests/ -v` and ensure all tests pass
2. **Pass all linting checks**: Run `uv run prek --all-files` to check code quality
3. **Include type hints**: Use Python 3.12+ union syntax (`str | None` instead of `Optional[str]`)
4. **Have docstrings**: All public functions and classes must have clear docstrings
5. **Follow project conventions**: Match existing code style and patterns

### Running Quality Checks

```bash
# Run all quality checks (prek handles multiple tools)
uv run prek --all-files

# Run tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_fishers_calculations.py -v

# Format code (prek auto-update)
uv run prek auto-update
```

## Making Changes

### Creating a Feature Branch

```bash
git checkout -b username/feature-description
```

Use descriptive branch names that indicate the feature or fix being implemented.

### Writing Tests

All new features and bug fixes must include tests. We use pytest for testing:

- Place test files in the `tests/` directory
- Name test files as `test_*.py`
- Use descriptive test function names: `test_<function_name>_<scenario>`
- Include docstrings explaining what the test validates

Example test structure:
```python
def test_calculate_p_value_valid_contingency_table():
    """Test p-value calculation with standard 2x2 contingency table."""
    a, b, c, d = 10, 5, 3, 2
    p_value, odds_ratio = calculate_p_value(a, b, c, d)
    assert p_value is not None
    assert 0 <= p_value <= 1
```

### Documenting Changes

- Add docstrings to all new functions and classes
- Update existing docstrings if changing function behavior
- Use clear, concise language in comments
- Link to relevant issues or papers in docstrings when applicable

### Committing Changes

Use clear, conventional commit messages:

```bash
git commit -m "feat: add new enrichment algorithm variant

Implement the new weighted enrichment calculation method described
in [paper reference]. Includes comprehensive test coverage for edge
cases.

Fixes #123"
```

Commit message format:
- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation updates
- **test**: Test additions or fixes
- **chore**: Configuration, dependencies, tooling
- **refactor**: Code refactoring without changing behavior

## Pull Request Process

1. **Update your branch** with latest changes:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Run all checks** before creating PR:
   ```bash
   uv run pytest tests/ -v
   uv run prek --all-files
   ```

3. **Push your changes**:
   ```bash
   git push origin username/feature-description
   ```

4. **Create a Pull Request** on GitHub with:
   - Clear description of changes
   - Reference to related issues
   - List of any breaking changes
   - Screenshots/results if relevant

5. **Address review feedback**: Respond to code review comments and update your PR as needed

## Testing Guidelines

### Test Coverage

- Aim for > 80% code coverage for critical paths
- All calculation functions must have tests
- Include edge cases: empty inputs, boundary values, invalid data

### Test Organization

- `test_fishers_calculations.py`: Fisher's exact test calculations
- `test_weighted_calculations.py`: Weighted enrichment calculations
- `test_visualization_pruning.py`: Graph pruning and visualization utilities
- `test_integration_enrichment.py`: End-to-end pipeline integration
- `test_*_calculations.py`: Module-specific tests

### Running Test Coverage

```bash
uv run pytest tests/ --cov=calculations --cov-report=html
# Open htmlcov/index.html to view coverage report
```

## Documentation Guidelines

### Docstring Format

Use Google-style docstrings:

```python
def run_enrichment_analysis(
    studyset_list: list[str],
    levels: int = 2,
    classification: str = "structural",
) -> tuple[dict, object]:
    """
    Run enrichment analysis on a study set.

    Performs Fisher's exact test enrichment analysis on the given study set,
    with optional graph pruning. Returns enriched terms and the pruned graph.

    Args:
        studyset_list: List of ChEBI IDs to analyze.
        levels: Distance threshold for root pruning (default: 2).
        classification: Type of ontology to use: "structural" or "functional".

    Returns:
        Tuple of (results dict containing enrichment data, pruned graph).

    Raises:
        FileNotFoundError: If required data files are missing.
        ValueError: If studyset_list is empty or contains invalid IDs.

    Example:
        >>> results, graph = run_enrichment_analysis(["CHEBI:123", "CHEBI:456"])
        >>> print(len(results["enrichment_results"]))
    """
```

## Reporting Issues

When reporting bugs, please include:

- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Your environment (Python version, OS, etc.)
- Relevant error messages or logs
- Minimal example code if applicable

## Performance Considerations

- Avoid loading the full ChEBI ontology in tests (use mocks or small test data)
- Profile code for performance-critical paths
- Document any known performance limitations
- Include benchmarking results for optimization PRs

## License

By contributing to ChEBI-N, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Open an issue on GitHub
- Check existing discussions for similar topics
- Email the maintainers

Thank you for contributing to ChEBI-N!
