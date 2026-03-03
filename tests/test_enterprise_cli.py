"""Tests for the garak-enterprise-assess unified CLI."""

from click.testing import CliRunner

from garak_enterprise.cli import DOMAIN_REGISTRY, LEGAL_PROBES, _parse_buffs, _resolve_probes, main


class TestDomainRegistry:

    def test_financial_domain_registered(self):
        assert "financial" in DOMAIN_REGISTRY

    def test_legal_domain_registered(self):
        assert "legal" in DOMAIN_REGISTRY

    def test_each_domain_has_probes(self):
        for name, info in DOMAIN_REGISTRY.items():
            assert "probes" in info
            assert len(info["probes"]) > 0

    def test_each_domain_has_label(self):
        for name, info in DOMAIN_REGISTRY.items():
            assert "label" in info
            assert len(info["label"]) > 0


class TestResolveProbes:

    def test_all_excludes_advanced(self):
        selected = _resolve_probes("all", LEGAL_PROBES)
        assert not any(k.startswith("advanced-") for k in selected)

    def test_all_includes_standard(self):
        selected = _resolve_probes("all", LEGAL_PROBES)
        assert len(selected) >= 5

    def test_full_includes_advanced(self):
        selected = _resolve_probes("full", LEGAL_PROBES)
        assert any(k.startswith("advanced-") for k in selected)

    def test_advanced_only_advanced(self):
        selected = _resolve_probes("advanced", LEGAL_PROBES)
        assert all(k.startswith("advanced-") for k in selected)
        assert len(selected) >= 1

    def test_specific_probe_selection(self):
        selected = _resolve_probes("advice", LEGAL_PROBES)
        assert selected == ["advice"]

    def test_comma_separated_selection(self):
        selected = _resolve_probes("advice,litigation", LEGAL_PROBES)
        assert "advice" in selected
        assert "litigation" in selected


class TestParseBufss:

    def test_none_preset(self):
        assert _parse_buffs("none") == []

    def test_light_preset(self):
        result = _parse_buffs("light")
        assert "base64" in result

    def test_custom_valid(self):
        result = _parse_buffs("base64,persona")
        assert result == ["base64", "persona"]


class TestEnterpriseCLIDryRun:

    def _dry_run(self, domain: str, probes: str = "all") -> tuple[int, str]:
        runner = CliRunner()
        result = runner.invoke(main, [
            "--domain", domain,
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test-model",
            "--probes", probes,
            "--dry-run",
        ])
        return result.exit_code, result.output

    def test_legal_domain_dry_run_exits_cleanly(self):
        exit_code, _ = self._dry_run("legal")
        assert exit_code == 0

    def test_financial_domain_dry_run_exits_cleanly(self):
        exit_code, _ = self._dry_run("financial")
        assert exit_code == 0

    def test_legal_dry_run_shows_legal_probes(self):
        _, output = self._dry_run("legal")
        assert "advice" in output or "privilege" in output or "litigation" in output

    def test_financial_dry_run_shows_financial_probes(self):
        _, output = self._dry_run("financial")
        assert "impartiality" in output or "misconduct" in output

    def test_invalid_domain_exits_nonzero(self):
        exit_code, _ = self._dry_run("unicorn")
        assert exit_code != 0

    def test_all_excludes_advanced_legal(self):
        _, output = self._dry_run("legal", probes="all")
        assert "advanced-advice" not in output
        assert "advanced-litigation" not in output

    def test_full_includes_advanced_legal(self):
        _, output = self._dry_run("legal", probes="full")
        assert "advanced-" in output

    def test_advanced_shows_only_advanced(self):
        _, output = self._dry_run("legal", probes="advanced")
        # Standard-only probes (no advanced variant) should not appear
        # "case-law" and "contract" have no advanced- prefix version
        assert "case-law" not in output
        assert "contract" not in output

    def test_multi_domain_dry_run(self):
        runner = CliRunner()
        result = runner.invoke(main, [
            "--domain", "financial,legal",
            "--target-url", "http://localhost:11434/v1",
            "--target-model", "test-model",
            "--dry-run",
        ])
        assert result.exit_code == 0
        assert "financial" in result.output.lower() or "impartiality" in result.output
        assert "legal" in result.output.lower() or "advice" in result.output

    def test_no_api_calls_message(self):
        _, output = self._dry_run("legal")
        assert "No API calls" in output
