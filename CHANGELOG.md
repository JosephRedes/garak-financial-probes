# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2024-02-07

### Added

#### LLM-as-Judge Detection
- `FinancialJudge` - LLM-based evaluation for nuanced compliance detection
- `HybridJudge` - Combines fast regex pre-filtering with LLM for edge cases
- Structured judgment output with dimension scores and reasoning
- Category-specific judge prompts for deeper analysis

#### Report Generation
- `ReportGenerator` - Generates markdown reports with:
  - Score distributions (ASCII charts)
  - High-concern examples with collapsible details
  - Methodology documentation
  - Per-category breakdowns
- `ResultAggregator` - Accumulates judgments across categories
- JSON export for further analysis

#### CLI Tool
- `garak-financial-assess` command for running assessments
- Progress bar with Rich console output
- Dry-run mode for testing configurations
- Environment variable support for credentials
- Summary table with color-coded results

#### Security Hardening
- `SecureLLMClient` with:
  - Environment-only credential loading (no hardcoded secrets)
  - Request timeouts and size limits
  - Retry logic with exponential backoff
  - No sensitive data in logs
- Input sanitization in judge prompts
- URL masking in reports

## [0.1.0] - 2024-02-07

### Added

#### Probes
- `financial.impartiality` - Tests for unauthorized investment advice
- `financial.misconduct` - Tests for market manipulation, insider trading
- `financial.disclosure` - Tests for MNPI leakage
- `financial.hallucination` - Tests for fabricated market data
- `financial.compliance` - Tests for SEC/FINRA/AML violations
- `financial.calculation` - Tests for financial math errors
- `financial.leakage` - Tests for proprietary data exposure
- `financial.sycophancy` - Tests for validation of risky decisions

#### Detectors
- `financial.advice` - Pattern-based investment recommendation detection
- `financial.misconduct` - Market manipulation detection
- `financial.factcheck` - Hallucinated data detection
- `financial.compliance` - Regulatory violation detection

#### Buffs (Prompt Augmentation)
- Encoding: Base64, ROT13, leetspeak, homoglyphs, mixed case
- Persona: Vulnerable users, authority figures, roleplay, urgency
- Financial: Entity swaps, amount variations, timeframe variations
- Jailbreak: Prefix, suffix, multi-turn, obfuscation

#### Infrastructure
- Garak plugin integration via entry points
- Example configurations for REST endpoints
- Enterprise configuration with full augmentation
- Comprehensive test suite
- GitHub Actions CI/CD pipeline
- Pre-commit hooks
- Dependabot and CodeQL security scanning

[Unreleased]: https://github.com/JosephRedes/garak-financial-probes/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/JosephRedes/garak-financial-probes/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/JosephRedes/garak-financial-probes/releases/tag/v0.1.0
