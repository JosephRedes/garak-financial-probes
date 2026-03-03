"""
Tests for the automation entry point (garak-financial-review).

Focuses on pure functions (_generate_consolidated_report) and
subprocess-mocked _run_garak, avoiding real network or LLM calls.
"""

from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from garak_financial.automation import (
    _generate_consolidated_report,
    _run_garak,
    main,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def clean_results():
    """Results dict where both components completed successfully."""
    return {
        "model": "test-llama3",
        "endpoint": "http://localhost:11434/v1",
        "timestamp": "20240101_120000",
        "garak": {
            "status": "completed",
            "probes_run": ["dan", "encoding"],
            "output_dir": "/tmp/garak_output",
            "return_code": 0,
        },
        "financial": {
            "status": "completed",
            "exit_code": 0,
            "report_path": "/tmp/financial_output/assessment_test.md",
            "json_path": "/tmp/financial_output/results_test.json",
            "data": {
                "overall_mean_score": 0.15,
                "total_prompts": 100,
                "judge_model": "gemma3:4b",
                "categories": {
                    "impartiality": {
                        "mean_score": 0.12,
                        "high_concern_count": 1,
                        "high_concern_pct": 1.0,
                    },
                },
            },
        },
    }


@pytest.fixture
def high_risk_results():
    """Results dict with a high financial risk score."""
    return {
        "model": "risky-model",
        "endpoint": "http://localhost:11434/v1",
        "timestamp": "20240101_120000",
        "garak": {"status": "completed", "probes_run": ["dan"], "return_code": 0},
        "financial": {
            "status": "completed",
            "exit_code": 0,
            "data": {"overall_mean_score": 0.75, "total_prompts": 50,
                     "judge_model": "judge", "categories": {}},
        },
    }


@pytest.fixture
def skipped_results():
    """Results dict where both components were skipped."""
    return {
        "model": "test-model",
        "endpoint": "http://localhost:11434/v1",
        "timestamp": "20240101_120000",
        "garak": None,
        "financial": None,
    }


# ---------------------------------------------------------------------------
# _generate_consolidated_report — pure function (file I/O only)
# ---------------------------------------------------------------------------

class TestGenerateConsolidatedReport:

    def test_creates_markdown_file(self, tmp_path, clean_results):
        path = _generate_consolidated_report(
            clean_results, tmp_path, "test_llama3", "20240101_120000",
        )
        assert path.exists()
        assert path.suffix == ".md"

    def test_filename_includes_model_and_timestamp(self, tmp_path, clean_results):
        path = _generate_consolidated_report(
            clean_results, tmp_path, "test_llama3", "20240101_120000",
        )
        assert "test_llama3" in path.name
        assert "20240101_120000" in path.name

    def test_report_contains_model_name(self, tmp_path, clean_results):
        path = _generate_consolidated_report(
            clean_results, tmp_path, "test_llama3", "20240101_120000",
        )
        content = path.read_text(encoding="utf-8")
        assert "test-llama3" in content

    def test_approve_recommendation_on_clean_results(self, tmp_path, clean_results):
        path = _generate_consolidated_report(
            clean_results, tmp_path, "test_llama3", "20240101_120000",
        )
        content = path.read_text(encoding="utf-8")
        assert "APPROVE" in content

    def test_requires_review_on_high_risk(self, tmp_path, high_risk_results):
        path = _generate_consolidated_report(
            high_risk_results, tmp_path, "risky_model", "20240101_120000",
        )
        content = path.read_text(encoding="utf-8")
        assert "REQUIRES REVIEW" in content or "CONDITIONAL" in content

    def test_skipped_sections_say_skipped(self, tmp_path, skipped_results):
        path = _generate_consolidated_report(
            skipped_results, tmp_path, "test_model", "20240101_120000",
        )
        content = path.read_text(encoding="utf-8")
        assert "Skipped" in content or "skipped" in content

    def test_report_contains_category_breakdown(self, tmp_path, clean_results):
        path = _generate_consolidated_report(
            clean_results, tmp_path, "test_llama3", "20240101_120000",
        )
        content = path.read_text(encoding="utf-8")
        assert "impartiality" in content

    def test_report_contains_methodology_section(self, tmp_path, clean_results):
        path = _generate_consolidated_report(
            clean_results, tmp_path, "test_llama3", "20240101_120000",
        )
        content = path.read_text(encoding="utf-8")
        assert "Methodology" in content

    def test_endpoint_is_masked_in_report(self, tmp_path, clean_results):
        """Sensitive endpoint paths should be masked."""
        results = dict(clean_results)
        results["endpoint"] = "http://internal.corp.com/v1/chat/completions"
        path = _generate_consolidated_report(
            results, tmp_path, "test", "20240101_120000",
        )
        content = path.read_text(encoding="utf-8")
        assert "chat/completions" not in content


# ---------------------------------------------------------------------------
# _run_garak — uses subprocess, so we mock it
# ---------------------------------------------------------------------------

class TestRunGarak:

    def test_returns_completed_on_zero_exit(self, tmp_path):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""

        with patch("garak_financial.automation.subprocess.run", return_value=mock_result):
            result = _run_garak("http://localhost:11434/v1", "llama3", tmp_path)

        assert result["status"] == "completed"
        assert result["return_code"] == 0

    def test_returns_failed_on_nonzero_exit(self, tmp_path):
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error"

        with patch("garak_financial.automation.subprocess.run", return_value=mock_result):
            result = _run_garak("http://localhost:11434/v1", "llama3", tmp_path)

        assert result["status"] == "failed"

    def test_returns_not_installed_when_garak_missing(self, tmp_path):
        with patch(
            "garak_financial.automation.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = _run_garak("http://localhost:11434/v1", "llama3", tmp_path)

        assert result["status"] == "not_installed"
        assert result["probes_run"] == []

    def test_returns_timeout_on_timeout(self, tmp_path):
        import subprocess

        with patch(
            "garak_financial.automation.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="garak", timeout=3600),
        ):
            result = _run_garak("http://localhost:11434/v1", "llama3", tmp_path)

        assert result["status"] == "timeout"

    def test_result_includes_probes_run(self, tmp_path):
        mock_result = MagicMock()
        mock_result.returncode = 0

        with patch("garak_financial.automation.subprocess.run", return_value=mock_result):
            result = _run_garak("http://localhost:11434/v1", "llama3", tmp_path)

        assert "probes_run" in result
        assert len(result["probes_run"]) > 0


# ---------------------------------------------------------------------------
# CLI entry point — skip-garak + skip-financial avoids all real calls
# ---------------------------------------------------------------------------

class TestAutomationCLI:

    def test_skip_both_completes_successfully(self, tmp_path):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test-model",
            "--output-dir", str(tmp_path),
            "--skip-garak",
            "--skip-financial",
        ])
        assert result.exit_code == 0

    def test_skip_both_creates_consolidated_report(self, tmp_path):
        runner = CliRunner()
        runner.invoke(main, [
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test-model",
            "--output-dir", str(tmp_path),
            "--skip-garak",
            "--skip-financial",
        ])
        md_files = list(tmp_path.glob("security_review_*.md"))
        assert len(md_files) == 1

    def test_skip_both_report_mentions_model(self, tmp_path):
        runner = CliRunner()
        runner.invoke(main, [
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "my-test-model",
            "--output-dir", str(tmp_path),
            "--skip-garak",
            "--skip-financial",
        ])
        md_files = list(tmp_path.glob("security_review_*.md"))
        content = md_files[0].read_text(encoding="utf-8")
        assert "my-test-model" in content
