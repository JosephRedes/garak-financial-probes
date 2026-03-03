"""
Tests for the CLI entry point (garak-financial-assess).

Covers buff parsing, probe selection logic, --dry-run, --vertex-ai,
and invalid input handling — all without making real API calls.
"""

from click.testing import CliRunner

from garak_financial.cli import PROBES, _parse_buff_selection, main


class TestBuffParsing:
    """Tests for _parse_buff_selection (pure function, no I/O)."""

    def test_none_preset_returns_empty(self):
        assert _parse_buff_selection("none") == []

    def test_light_preset_contains_expected_buffs(self):
        result = _parse_buff_selection("light")
        assert "base64" in result
        assert "persona" in result

    def test_standard_preset_contains_expected_buffs(self):
        result = _parse_buff_selection("standard")
        assert "base64" in result
        assert "jailbreak_prefix" in result

    def test_full_preset_returns_all_buffs(self):
        result = _parse_buff_selection("full")
        assert len(result) > 5
        assert "base64" in result
        assert "obfuscated" in result

    def test_custom_comma_separated(self):
        result = _parse_buff_selection("base64,rot13")
        assert result == ["base64", "rot13"]

    def test_case_insensitive(self):
        assert _parse_buff_selection("NONE") == []
        assert _parse_buff_selection("Light") == _parse_buff_selection("light")


class TestProbeSelectionDryRun:
    """Test probe selection via --dry-run (no API calls made)."""

    def _dry_run(self, probes: str) -> tuple[int, str]:
        runner = CliRunner()
        result = runner.invoke(main, [
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test-model",
            "--probes", probes,
            "--dry-run",
        ])
        return result.exit_code, result.output

    def test_all_excludes_advanced_probes(self):
        exit_code, output = self._dry_run("all")
        assert exit_code == 0
        for adv in ["advanced-impartiality", "advanced-misconduct",
                    "advanced-disclosure", "advanced-compliance", "advanced-sycophancy"]:
            assert adv not in output

    def test_all_includes_standard_probes(self):
        exit_code, output = self._dry_run("all")
        assert exit_code == 0
        for std in ["impartiality", "misconduct", "disclosure",
                    "hallucination", "compliance", "calculation", "leakage", "sycophancy"]:
            assert std in output

    def test_full_includes_advanced_probes(self):
        exit_code, output = self._dry_run("full")
        assert exit_code == 0
        assert "advanced-impartiality" in output
        assert "advanced-sycophancy" in output

    def test_full_includes_standard_probes(self):
        exit_code, output = self._dry_run("full")
        assert exit_code == 0
        assert "impartiality" in output
        assert "hallucination" in output

    def test_advanced_group_alias_expands(self):
        exit_code, output = self._dry_run("advanced")
        assert exit_code == 0
        assert "advanced-impartiality" in output
        assert "advanced-sycophancy" in output

    def test_advanced_group_alias_excludes_standard_only_probes(self):
        exit_code, output = self._dry_run("advanced")
        assert exit_code == 0
        # calculation and leakage have no advanced variant — should not appear
        assert "calculation" not in output
        assert "leakage" not in output

    def test_single_probe_selection(self):
        exit_code, output = self._dry_run("impartiality")
        assert exit_code == 0
        assert "impartiality" in output

    def test_comma_separated_probes(self):
        exit_code, output = self._dry_run("impartiality,misconduct")
        assert exit_code == 0
        assert "impartiality" in output
        assert "misconduct" in output

    def test_invalid_probe_exits_nonzero(self):
        exit_code, _ = self._dry_run("nonexistent_probe")
        assert exit_code != 0

    def test_all_probe_count_is_eight(self):
        """'all' should select exactly the 8 standard probes."""
        standard_probes = [k for k in PROBES if not k.startswith("advanced-")]
        assert len(standard_probes) == 8

    def test_full_probe_count_is_thirteen(self):
        """'full' should select all 13 probes."""
        assert len(PROBES) == 13


class TestVertexAiFlag:
    """Test the --vertex-ai guidance flag."""

    def test_vertex_ai_exits_cleanly(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--vertex-ai",
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test",
        ])
        assert result.exit_code == 0

    def test_vertex_ai_prints_guidance(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--vertex-ai",
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test",
        ])
        assert "Vertex AI" in result.output
        assert "gcloud" in result.output

    def test_vertex_ai_does_not_start_assessment(self):
        """--vertex-ai should exit before any API calls or probe loading."""
        runner = CliRunner()
        result = runner.invoke(main, [
            "--vertex-ai",
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test",
        ])
        # Should not mention assessment-specific output
        assert "Assessing" not in result.output
        assert "LLM clients" not in result.output


class TestDryRunOutput:
    """Test --dry-run mode produces useful output."""

    def test_dry_run_shows_probe_name(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test",
            "--probes", "impartiality",
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "impartiality" in result.output

    def test_dry_run_shows_no_api_calls_message(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test",
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "No API calls" in result.output

    def test_dry_run_with_buffs_shows_buff_names(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test",
            "--probes", "impartiality",
            "--buffs", "light",
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "base64" in result.output or "persona" in result.output
