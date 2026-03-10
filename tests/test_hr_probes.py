"""Tests for the garak_hr probe suite."""

import pytest

from garak_hr.probes import (
    HR_PROBES,
    AdvancedCompensationLeakage,
    AdvancedEmployeeDataPrivacy,
    AdvancedProtectedClassBias,
    CompensationLeakage,
    EmployeeDataPrivacy,
    HostileWorkplace,
    ProtectedClassBias,
    UnauthorizedTerminationAdvice,
)

STANDARD_PROBE_CLASSES = [
    ProtectedClassBias,
    EmployeeDataPrivacy,
    UnauthorizedTerminationAdvice,
    CompensationLeakage,
    HostileWorkplace,
]

ADVANCED_PROBE_CLASSES = [
    AdvancedProtectedClassBias,
    AdvancedEmployeeDataPrivacy,
    AdvancedCompensationLeakage,
]

ALL_PROBE_CLASSES = STANDARD_PROBE_CLASSES + ADVANCED_PROBE_CLASSES


class TestHRProbeStructure:
    """All HR probes must have required Garak attributes."""

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
        assert "hr" in probe.tags

    def test_has_primary_detector(self, probe):
        assert hasattr(probe, "primary_detector")
        assert probe.primary_detector.startswith("hr.")

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


class TestProtectedClassBiasProbe:

    def test_covers_interview_questions(self):
        probe = ProtectedClassBias()
        text = " ".join(probe.prompts).lower()
        assert "interview" in text

    def test_covers_protected_classes(self):
        probe = ProtectedClassBias()
        text = " ".join(probe.prompts).lower()
        assert any(
            cls in text
            for cls in ["age", "disability", "pregnant", "religion", "medical"]
        )

    def test_covers_screening_criteria(self):
        probe = ProtectedClassBias()
        text = " ".join(probe.prompts).lower()
        assert "screen" in text or "filter" in text or "exclude" in text

    def test_advanced_uses_proxy_framing(self):
        probe = AdvancedProtectedClassBias()
        text = " ".join(probe.prompts).lower()
        assert "zip code" in text or "neighborhood" in text or "name" in text


class TestEmployeeDataPrivacyProbe:

    def test_covers_medical_data(self):
        probe = EmployeeDataPrivacy()
        text = " ".join(probe.prompts).lower()
        assert "medical" in text or "health" in text or "hipaa" in text

    def test_covers_surveillance(self):
        probe = EmployeeDataPrivacy()
        text = " ".join(probe.prompts).lower()
        assert "email" in text or "keystrokes" in text or "slack" in text or "screenshot" in text

    def test_advanced_uses_authority_framing(self):
        probe = AdvancedEmployeeDataPrivacy()
        text = " ".join(probe.prompts).lower()
        assert (
            "hr director" in text
            or "ciso" in text
            or "authorized" in text
            or "legal counsel" in text
            or "compliance officer" in text
            or "executive" in text
        )


class TestUnauthorizedTerminationAdviceProbe:

    def test_covers_paper_trail(self):
        probe = UnauthorizedTerminationAdvice()
        text = " ".join(probe.prompts).lower()
        assert "paper trail" in text or "documentation" in text or "document" in text

    def test_covers_fmla_leave(self):
        probe = UnauthorizedTerminationAdvice()
        text = " ".join(probe.prompts).lower()
        assert "fmla" in text or "leave" in text

    def test_covers_pip_design(self):
        probe = UnauthorizedTerminationAdvice()
        text = " ".join(probe.prompts).lower()
        assert "pip" in text or "performance improvement" in text

    def test_covers_warn_act(self):
        probe = UnauthorizedTerminationAdvice()
        text = " ".join(probe.prompts).lower()
        assert "warn" in text


class TestCompensationLeakageProbe:

    def test_covers_salary_bands(self):
        probe = CompensationLeakage()
        text = " ".join(probe.prompts).lower()
        assert "salary" in text or "pay" in text or "compensation" in text

    def test_covers_executive_pay(self):
        probe = CompensationLeakage()
        text = " ".join(probe.prompts).lower()
        assert "executive" in text or "ceo" in text or "bonus" in text

    def test_advanced_uses_authority_escalation(self):
        probe = AdvancedCompensationLeakage()
        text = " ".join(probe.prompts).lower()
        assert (
            "compensation committee" in text
            or "board" in text
            or "proxy" in text
            or "authorized" in text
        )


class TestHostileWorkplaceProbe:

    def test_covers_harassment(self):
        probe = HostileWorkplace()
        text = " ".join(probe.prompts).lower()
        assert "harass" in text or "hostile" in text

    def test_covers_retaliation(self):
        probe = HostileWorkplace()
        text = " ".join(probe.prompts).lower()
        assert "retaliat" in text or "complaint" in text


class TestHRProbesRegistry:

    def test_registry_has_standard_probes(self):
        standard = [k for k in HR_PROBES if not k.startswith("advanced-")]
        assert len(standard) >= 4

    def test_registry_has_advanced_probes(self):
        advanced = [k for k in HR_PROBES if k.startswith("advanced-")]
        assert len(advanced) >= 3

    def test_all_registry_values_are_probe_classes(self):
        for key, cls in HR_PROBES.items():
            probe = cls()
            assert hasattr(probe, "prompts")
            assert hasattr(probe, "tags")
