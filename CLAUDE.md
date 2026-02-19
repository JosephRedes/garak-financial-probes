# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`garak-financial-probes` is a Python plugin for [NVIDIA Garak](https://github.com/NVIDIA/garak) that red-teams LLMs for financial services safety. It tests whether a **target model** (the LLM under evaluation) produces unsafe financial outputs, using a separate **judge model** to score responses.

## Commands

```bash
# Install for development
pip install -e ".[dev]"

# Run all tests
pytest

# Run a single test file
pytest tests/test_probes.py

# Run with coverage
pytest --cov=garak_financial --cov-report=xml

# Lint and format
ruff check .
ruff check --fix .
ruff format .

# Type checking
mypy garak_financial --ignore-missing-imports

# Run the financial assessment CLI
garak-financial-assess \
  --target-url http://localhost:11434/v1 \
  --target-model llama3:8b \
  --judge-model gemma3:4b \
  --probes all \
  --output-dir ./reports

# Run the full automated review (Garak + financial probes + consolidated report)
garak-financial-review \
  --target-url http://localhost:11434/v1 \
  --target-model llama3:8b \
  --judge-model gemma3:4b
```

## Architecture

The package registers itself with Garak via `pyproject.toml` entry points (`garak.probes`, `garak.detectors`, `garak.buffs`).

### Core Evaluation Pipeline

```
Attack Prompts (Probes) → [Buff Augmentation] → Target LLM → Response
                                                                  ↓
                                               Detector (regex) + Judge (LLM) → Score
```

**Two evaluation methods run in parallel:**
1. **Detectors** (`garak_financial/detectors/`) — fast regex pattern matching, no LLM needed
2. **Judges** (`garak_financial/judges/`) — `FinancialJudge` sends responses to a separate LLM and parses JSON scores across 6 dimensions (investment_advice, price_prediction, confidentiality, regulatory_concern, factual_accuracy, sycophancy). `HybridJudge` uses regex first and falls back to the LLM only for ambiguous cases.

### Probe Categories

8 probe classes in `garak_financial/probes/`, each inheriting from `garak.probes.base.Probe`:
`impartiality`, `misconduct`, `disclosure`, `hallucination`, `compliance`, `calculation`, `leakage`, `sycophancy`

### Buff System

`garak_financial/buffs/` transforms base prompts to amplify test coverage:
- **encoding** — base64, ROT13, leetspeak, unicode homoglyphs
- **persona** — vulnerable user variants, authority roleplay, urgency pressure
- **financial** — entity/amount/timeframe substitutions
- **jailbreak** — prefix/suffix injection, obfuscation

Presets: `none` (1x), `light` (~5x), `standard` (~20x), `full` (~50x)

### Security Patterns

`SecureLLMClient` in `garak_financial/utils/` enforces: API keys from environment only, 60s timeouts, 1MB response cap, no redirects (SSRF prevention), 3-attempt retry with typed errors (`LLMAuthenticationError`, `LLMRateLimitError`, `LLMTimeoutError`, `LLMResponseError`).

### Reporting

`garak_financial/reporting/` aggregates `FinancialJudgment` objects into `CategoryResult` → `AssessmentResult`, then `ReportGenerator` outputs markdown + JSON with score distributions and APPROVE/CONDITIONAL/DENY recommendations.

## Adding New Probes or Detectors

- Probes inherit from `garak.probes.base.Probe` and must define `name`, `description`, `prompts`, `tags`
- Detectors inherit from `garak.detectors.base.Detector` and use regex patterns against response text
- Export new classes from the respective `__init__.py`

## Key Files

- `pyproject.toml` — package metadata, entry points, ruff/mypy/pytest config
- `garak_financial/judges/financial.py` — judge prompt templates and scoring logic
- `garak_financial/cli/__init__.py` — `garak-financial-assess` entry point (Rich UI)
- `garak_financial/automation/__init__.py` — `garak-financial-review` pipeline
- `PERSONAL_NOTES.md` — detailed developer reference with data flow diagrams
