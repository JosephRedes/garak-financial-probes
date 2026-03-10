"""Tests for the garak_risk probe suite."""

import pytest

from garak_risk.probes import (
    RISK_PROBES,
    AdvancedCreditRiskMisrepresentation,
    AdvancedModelRiskGuidance,
    AdvancedRegulatoryCapitalAdvice,
    CreditRiskMisrepresentation,
    ModelRiskGuidance,
    OperationalRiskEvasion,
    RegulatoryCapitalAdvice,
    StressTestFabrication,
)

STANDARD_PROBE_CLASSES = [
    ModelRiskGuidance,
    CreditRiskMisrepresentation,
    StressTestFabrication,
    OperationalRiskEvasion,
    RegulatoryCapitalAdvice,
]

ADVANCED_PROBE_CLASSES = [
    AdvancedModelRiskGuidance,
    AdvancedCreditRiskMisrepresentation,
    AdvancedRegulatoryCapitalAdvice,
]

ALL_PROBE_CLASSES = STANDARD_PROBE_CLASSES + ADVANCED_PROBE_CLASSES


class TestRiskProbeStructure:
    """All risk probes must have required Garak attributes."""

    @pytest.fixture(params=ALL_PROBE_CLASSES, ids=lambda c: c.__name__)
    def probe(self, request):
        return request.param()

    def test_has_bcp47(self, probe):
        assert hasattr(probe, "bcp47")
        assert probe.bcp47 == "en"

    def test_has_goal(self, probe):
        assert hasattr(probe, "goal")
        assert len(probe.goal) > 10

    def test_has_prompts(self, probe):
        assert hasattr(probe, "prompts")
        assert len(probe.prompts) >= 6

    def test_has_tags(self, probe):
        assert hasattr(probe, "tags")
        assert "risk" in probe.tags

    def test_has_primary_detector(self, probe):
        assert hasattr(probe, "primary_detector")
        assert probe.primary_detector.startswith("risk.")

    def test_prompts_are_strings(self, probe):
        for p in probe.prompts:
            assert isinstance(p, str)
            assert len(p) > 20


class TestAdvancedProbesTags:
    """Advanced probes must carry the 'advanced' tag."""

    @pytest.fixture(params=ADVANCED_PROBE_CLASSES, ids=lambda c: c.__name__)
    def probe(self, request):
        return request.param()

    def test_has_advanced_tag(self, probe):
        assert "advanced" in probe.tags


class TestModelRiskGuidanceProbe:

    def test_covers_sr_11_7(self):
        probe = ModelRiskGuidance()
        text = " ".join(probe.prompts).lower()
        assert "sr 11-7" in text or "sr11-7" in text

    def test_covers_validation_methodology(self):
        probe = ModelRiskGuidance()
        text = " ".join(probe.prompts).lower()
        assert "validation" in text or "validate" in text

    def test_covers_performance_thresholds(self):
        probe = ModelRiskGuidance()
        text = " ".join(probe.prompts).lower()
        assert "gini" in text or "psi" in text or "auc" in text or "ks" in text

    def test_covers_model_documentation(self):
        probe = ModelRiskGuidance()
        text = " ".join(probe.prompts).lower()
        assert "documentation" in text or "document" in text

    def test_advanced_uses_authority_framing(self):
        probe = AdvancedModelRiskGuidance()
        text = " ".join(probe.prompts).lower()
        assert (
            "examiner" in text
            or "federal reserve" in text
            or "occ" in text
            or "committee" in text
        )


class TestCreditRiskMisrepresentationProbe:

    def test_covers_credit_approval_decisions(self):
        probe = CreditRiskMisrepresentation()
        text = " ".join(probe.prompts).lower()
        assert "approve" in text or "decline" in text or "deny" in text

    def test_covers_credit_score_thresholds(self):
        probe = CreditRiskMisrepresentation()
        text = " ".join(probe.prompts).lower()
        assert (
            "fico" in text
            or "credit score" in text
            or "dscr" in text
            or "debt-to-income" in text
        )

    def test_covers_probability_of_default(self):
        probe = CreditRiskMisrepresentation()
        text = " ".join(probe.prompts).lower()
        assert "probability of default" in text or "pd" in text

    def test_advanced_uses_underwriter_persona(self):
        probe = AdvancedCreditRiskMisrepresentation()
        text = " ".join(probe.prompts).lower()
        assert (
            "underwriter" in text
            or "loan officer" in text
            or "credit committee" in text
            or "credit officer" in text
        )


class TestStressTestFabricationProbe:

    def test_covers_stress_test_scenarios(self):
        probe = StressTestFabrication()
        text = " ".join(probe.prompts).lower()
        assert "stress test" in text or "scenario" in text

    def test_covers_regulatory_stress_tests(self):
        probe = StressTestFabrication()
        text = " ".join(probe.prompts).lower()
        assert "dfast" in text or "ccar" in text or "federal reserve" in text or "fed" in text


class TestOperationalRiskEvasionProbe:

    def test_covers_operational_risk(self):
        probe = OperationalRiskEvasion()
        text = " ".join(probe.prompts).lower()
        assert "operational risk" in text or "operational" in text

    def test_covers_incident_reporting(self):
        probe = OperationalRiskEvasion()
        text = " ".join(probe.prompts).lower()
        assert "incident" in text or "report" in text or "loss" in text


class TestRegulatoryCapitalAdviceProbe:

    def test_covers_capital_ratios(self):
        probe = RegulatoryCapitalAdvice()
        text = " ".join(probe.prompts).lower()
        assert "capital" in text and ("ratio" in text or "requirement" in text)

    def test_covers_basel_framework(self):
        probe = RegulatoryCapitalAdvice()
        text = " ".join(probe.prompts).lower()
        assert "basel" in text or "tier 1" in text or "rwa" in text

    def test_advanced_uses_examiner_framing(self):
        probe = AdvancedRegulatoryCapitalAdvice()
        text = " ".join(probe.prompts).lower()
        assert (
            "examiner" in text
            or "regulator" in text
            or "supervisor" in text
            or "fdic" in text
            or "occ" in text
        )


class TestRiskProbesRegistry:

    def test_registry_has_standard_probes(self):
        standard = [k for k in RISK_PROBES if not k.startswith("advanced-")]
        assert len(standard) >= 4

    def test_registry_has_advanced_probes(self):
        advanced = [k for k in RISK_PROBES if k.startswith("advanced-")]
        assert len(advanced) >= 3

    def test_all_registry_values_are_probe_classes(self):
        for key, cls in RISK_PROBES.items():
            probe = cls()
            assert hasattr(probe, "prompts")
            assert hasattr(probe, "tags")
