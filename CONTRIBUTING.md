# Contributing to garak-financial-probes

Thank you for your interest in contributing to this project! This document provides guidelines for contributions.

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/JosephRedes/garak-financial-probes.git
   cd garak-financial-probes
   ```
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

### Running Tests

```bash
pytest
```

### Code Quality

We use ruff for linting and formatting:

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check --fix .

# Format code
ruff format .
```

### Type Checking

```bash
mypy garak_financial
```

## Adding New Probes

1. Create a new file in `garak_financial/probes/`
2. Inherit from `garak.probes.base.Probe`
3. Implement required attributes:
   - `bcp47`: Language code (e.g., "en")
   - `goal`: What the probe is trying to elicit
   - `prompts`: List of test prompts
   - `tags`: List of relevant tags (include "financial")
4. Specify `primary_detector`
5. Add to `garak_financial/probes/__init__.py`
6. Write tests in `tests/test_probes.py`

Example:
```python
from garak.probes.base import Probe

class MyNewProbe(Probe):
    bcp47 = "en"
    goal = "elicit [specific vulnerability]"
    tags = ["financial", "my-category"]
    primary_detector = ["financial.my_detector"]
    
    prompts = [
        "Your test prompt 1",
        "Your test prompt 2",
    ]
```

## Adding New Detectors

1. Create a new file in `garak_financial/detectors/`
2. Inherit from `garak.detectors.base.Detector`
3. Implement the `detect(self, attempt)` method
4. Return a list of floats (0.0 = safe, 1.0 = vulnerability triggered)
5. Add to `garak_financial/detectors/__init__.py`
6. Write tests in `tests/test_detectors.py`

## Prompt Guidelines

When adding prompts:
- Cover diverse scenarios and phrasings
- Include both direct and indirect attempts
- Consider edge cases
- Reference real regulatory requirements where possible
- Do not include actual harmful instructions

## Pull Request Process

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Make your changes
3. Run tests and linting:
   ```bash
   pytest
   ruff check .
   ```
4. Commit with descriptive messages
5. Push and create a Pull Request

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming environment

## Questions?

Open an issue for questions or suggestions!
