"""Tests for the garak_legal probe suite."""

import pytest

from garak_legal.probes import (
    LEGAL_PROBES,
    AdvancedConfidentialMatterDisclosure,
    AdvancedLitigationStrategy,
    AdvancedPrivilegeLeakage,
    AdvancedUnauthorizedLegalAdvice,
    CaseLawHallucination,
    ConfidentialMatterDisclosure,
    ContractFabrication,
    LitigationStrategy,
    PrivilegeLeakage,
    UnauthorizedLegalAdvice,
)

STANDARD_PROBE_CLASSES = [
    UnauthorizedLegalAdvice,
    PrivilegeLeakage,
    CaseLawHallucination,
    ContractFabrication,
    LitigationStrategy,
    ConfidentialMatterDisclosure,
]

ADVANCED_PROBE_CLASSES = [
    AdvancedUnauthorizedLegalAdvice,
    AdvancedPrivilegeLeakage,
    AdvancedLitigationStrategy,
    AdvancedConfidentialMatterDisclosure,
]

ALL_PROBE_CLASSES = STANDARD_PROBE_CLASSES + ADVANCED_PROBE_CLASSES


class TestLegalProbeStructure:
    """All legal probes must have required Garak attributes."""

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
        assert "legal" in probe.tags

    def test_has_primary_detector(self, probe):
        assert hasattr(probe, "primary_detector")
        assert probe.primary_detector.startswith("legal.")

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


class TestUnauthorizedLegalAdviceProbe:

    def test_covers_employment_law(self):
        probe = UnauthorizedLegalAdvice()
        text = " ".join(probe.prompts).lower()
        assert "terminat" in text or "employment" in text

    def test_covers_contract_disputes(self):
        probe = UnauthorizedLegalAdvice()
        text = " ".join(probe.prompts).lower()
        assert "contract" in text or "agreement" in text

    def test_covers_liability_scenarios(self):
        probe = UnauthorizedLegalAdvice()
        text = " ".join(probe.prompts).lower()
        assert "liable" in text or "liability" in text or "sue" in text

    def test_advanced_uses_authority_framing(self):
        probe = AdvancedUnauthorizedLegalAdvice()
        text = " ".join(probe.prompts).lower()
        assert (
            "counsel" in text
            or "attorney" in text
            or "outside counsel" in text
            or "authorized" in text
        )


class TestPrivilegeLeakageProbe:

    def test_covers_privilege_invocation(self):
        probe = PrivilegeLeakage()
        text = " ".join(probe.prompts).lower()
        assert "privilege" in text or "privileged" in text

    def test_covers_attorney_client_relationship(self):
        probe = PrivilegeLeakage()
        text = " ".join(probe.prompts).lower()
        assert "attorney" in text or "counsel" in text or "lawyer" in text

    def test_advanced_uses_insider_framing(self):
        probe = AdvancedPrivilegeLeakage()
        text = " ".join(probe.prompts).lower()
        assert (
            "co-counsel" in text
            or "engagement" in text
            or "managing partner" in text
            or "prior" in text
        )


class TestCaseLawHallucinationProbe:

    def test_requests_specific_citations(self):
        probe = CaseLawHallucination()
        text = " ".join(probe.prompts).lower()
        assert "cite" in text or "citation" in text or "case" in text

    def test_requests_statute_text(self):
        probe = CaseLawHallucination()
        text = " ".join(probe.prompts).lower()
        assert "statute" in text or "section" in text or "quote" in text or "§" in text

    def test_requests_regulatory_guidance(self):
        probe = CaseLawHallucination()
        text = " ".join(probe.prompts).lower()
        assert any(
            agency in text
            for agency in ["sec", "eeoc", "ftc", "nlrb", "osha", "doj", "cfpb"]
        )


class TestContractFabricationProbe:

    def test_requests_contract_drafting(self):
        probe = ContractFabrication()
        text = " ".join(probe.prompts).lower()
        assert "draft" in text or "write" in text or "generate" in text

    def test_covers_nda_or_noncompete(self):
        probe = ContractFabrication()
        text = " ".join(probe.prompts).lower()
        assert "nda" in text or "non-compete" in text or "non-disclosure" in text


class TestLitigationStrategyProbe:

    def test_covers_plaintiff_strategy(self):
        probe = LitigationStrategy()
        text = " ".join(probe.prompts).lower()
        assert "sue" in text or "litigation" in text or "lawsuit" in text

    def test_covers_defense_strategy(self):
        probe = LitigationStrategy()
        text = " ".join(probe.prompts).lower()
        assert "defense" in text or "defend" in text or "defendant" in text

    def test_advanced_uses_professional_roleplay(self):
        probe = AdvancedLitigationStrategy()
        text = " ".join(probe.prompts).lower()
        assert (
            "outside counsel" in text
            or "litigation counsel" in text
            or "coach" in text
            or "doj" in text
        )


class TestLegalProbesRegistry:

    def test_registry_has_standard_probes(self):
        standard = [k for k in LEGAL_PROBES if not k.startswith("advanced-")]
        assert len(standard) >= 5

    def test_registry_has_advanced_probes(self):
        advanced = [k for k in LEGAL_PROBES if k.startswith("advanced-")]
        assert len(advanced) >= 4

    def test_all_registry_values_are_probe_classes(self):
        for key, cls in LEGAL_PROBES.items():
            probe = cls()
            assert hasattr(probe, "prompts")
            assert hasattr(probe, "tags")
