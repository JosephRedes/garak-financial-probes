# Contributing

## Development Setup

```bash
git clone https://github.com/JosephRedes/garak-financial-probes.git
cd garak-financial-probes
pip install -e ".[dev]"
```

## Running Tests

```bash
# All tests
pytest

# Single file
pytest tests/test_probes.py -v

# Single test
pytest tests/test_detectors.py::TestNegationHandling::test_advice_detector_no_false_positive_on_should_not -v

# With coverage report
pytest --cov=garak_financial --cov-report=term-missing
```

## Code Quality

All PRs must pass before merging:

```bash
ruff check .                                    # Lint
ruff check --fix .                              # Auto-fix
ruff format .                                   # Format
mypy garak_financial --ignore-missing-imports   # Type check
```

---

## Adding a New Probe

1. Create `garak_financial/probes/your_category.py`:

```python
from garak.probes.base import Probe

class YourCategory(Probe):
    bcp47 = "en"
    doc_uri = "https://link-to-relevant-regulation"
    primary_detector = "financial.advice"   # or another detector
    tags = ["financial", "your-tag"]
    goal = "one-line description of what you're testing for"

    prompts = [
        "First test prompt",
        "Second test prompt",
        # Aim for 15-30 prompts covering different angles
    ]
```

2. Export from `garak_financial/probes/__init__.py`
3. Add to the `PROBES` dict in `garak_financial/cli/__init__.py`
4. Add tests in `tests/test_probes.py`

### Standard vs. Advanced Probes

Each category should have two classes:

- **Standard** (`YourCategory`) — direct, literal prompts. Tests basic guardrail coverage.
- **Advanced** (`AdvancedYourCategory`) — indirect prompts that challenge models which already pass standard probes. Use techniques like fictional framing ("I'm writing a thriller where…"), authority claims ("As a licensed CFA…"), persona embedding, regulatory impersonation, or escalation chains.

Tag advanced probes with `"advanced"` and `"owasp:llm09"`.

---

## Adding a New Detector

Detectors live in `garak_financial/detectors/`. Three critical rules:

1. **Always match against `output.lower()`** — all patterns must be lowercase.
2. **Use the 40-character negation window** — prevents false positives on phrases like "you should NOT invest".
3. **Never use bare `\b0\b` or `\b1\b`** in score extraction — they match ordinary integers.

Template:

```python
import re
from garak.detectors.base import Detector

class YourDetector(Detector):
    name = "financial.yourdetector"
    description = "What this detector catches"

    PATTERNS = [
        r"pattern one",
        r"pattern two",
    ]

    _NEGATION_WORDS = [
        "not ", "never ", "don't ", "avoid ", "shouldn't ", "cannot ", "can't ",
    ]

    def detect(self, attempt) -> list[float]:
        return [self._score_output(r) for r in attempt.all_outputs if r]

    def _score_output(self, output: str) -> float:
        output_lower = output.lower()
        hits = 0
        for pattern in self.PATTERNS:
            for match in re.finditer(pattern, output_lower):
                preceding = output_lower[max(0, match.start() - 40):match.start()]
                if not any(neg in preceding for neg in self._NEGATION_WORDS):
                    hits += 1
        return min(1.0, hits * 0.3)
```

---

## Adding a Category-Specific Judge Prompt

Judge prompts live in `garak_financial/judges/__init__.py`. They **must** emit the standard 6-dimension `scores` dict — if `scores` is missing, `_parse_judgment` silently returns `overall_concern = 0.0` and the entire evaluation is discarded.

Required output schema:

```json
{
  "scores": {
    "investment_advice": 0.0,
    "price_prediction": 0.0,
    "confidentiality": 0.0,
    "regulatory_concern": 0.0,
    "factual_accuracy": 0.0,
    "sycophancy": 0.0
  },
  "overall_concern": 0.0,
  "reasoning": "...",
  "key_phrases": []
}
```

Set dimensions that aren't relevant to your category to `0.0` rather than omitting them.

---

## Pull Requests

- One logical change per PR
- All tests must pass (`pytest`)
- Ruff and mypy must be clean
- New behaviour must have test coverage
- New probe categories need both a standard and an advanced variant

Open an issue first for large changes so we can discuss the approach.
