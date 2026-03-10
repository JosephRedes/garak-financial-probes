"""Tests for the garak_corpfin probe suite."""

import pytest

from garak_corpfin.probes import (
    CORPFIN_PROBES,
    AdvancedEarningsManipulation,
    AdvancedInsiderInfo,
    AdvancedMADisclosure,
    BoardConfidentiality,
    EarningsManipulation,
    InsiderInfo,
    MADisclosure,
    ValuationFabrication,
)

STANDARD_PROBE_CLASSES = [
    MADisclosure,
    EarningsManipulation,
    ValuationFabrication,
    InsiderInfo,
    BoardConfidentiality,
]

ADVANCED_PROBE_CLASSES = [
    AdvancedMADisclosure,
    AdvancedEarningsManipulation,
    AdvancedInsiderInfo,
]

ALL_PROBE_CLASSES = STANDARD_PROBE_CLASSES + ADVANCED_PROBE_CLASSES


class TestCorpFinProbeStructure:
    """All corpfin probes must have required Garak attributes."""

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
        assert "corpfin" in probe.tags

    def test_has_primary_detector(self, probe):
        assert hasattr(probe, "primary_detector")
        assert probe.primary_detector.startswith("corpfin.")

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


class TestMADisclosureProbe:

    def test_covers_deal_terms(self):
        probe = MADisclosure()
        text = " ".join(probe.prompts).lower()
        assert "deal" in text or "transaction" in text or "merger" in text

    def test_covers_synergy_requests(self):
        probe = MADisclosure()
        text = " ".join(probe.prompts).lower()
        assert "synerg" in text

    def test_covers_breakup_fees(self):
        probe = MADisclosure()
        text = " ".join(probe.prompts).lower()
        assert "break" in text or "termination fee" in text

    def test_covers_merger_timeline(self):
        probe = MADisclosure()
        text = " ".join(probe.prompts).lower()
        assert "close" in text or "timeline" in text

    def test_advanced_uses_banker_persona(self):
        probe = AdvancedMADisclosure()
        text = " ".join(probe.prompts).lower()
        assert (
            "banker" in text
            or "advisor" in text
            or "deal team" in text
            or "fairness opinion" in text
        )


class TestEarningsManipulationProbe:

    def test_covers_revenue_recognition(self):
        probe = EarningsManipulation()
        text = " ".join(probe.prompts).lower()
        assert "revenue" in text and ("recognize" in text or "recognition" in text)

    def test_covers_reserve_adjustments(self):
        probe = EarningsManipulation()
        text = " ".join(probe.prompts).lower()
        assert "reserve" in text or "accrual" in text or "provision" in text

    def test_covers_quarter_end_pressure(self):
        probe = EarningsManipulation()
        text = " ".join(probe.prompts).lower()
        assert "quarter" in text

    def test_advanced_uses_controller_framing(self):
        probe = AdvancedEarningsManipulation()
        text = " ".join(probe.prompts).lower()
        assert (
            "controller" in text
            or "cfo" in text
            or "audit committee" in text
            or "auditor" in text
            or "accounting" in text
        )


class TestValuationFabricationProbe:

    def test_covers_dcf_manipulation(self):
        probe = ValuationFabrication()
        text = " ".join(probe.prompts).lower()
        assert "dcf" in text or "discount" in text or "terminal value" in text

    def test_covers_predetermined_valuation(self):
        probe = ValuationFabrication()
        text = " ".join(probe.prompts).lower()
        assert (
            "justify" in text
            or "reach" in text
            or "target" in text
            or "support" in text
        )

    def test_covers_comparable_analysis(self):
        probe = ValuationFabrication()
        text = " ".join(probe.prompts).lower()
        assert "comp" in text or "multiple" in text or "ebitda" in text


class TestInsiderInfoProbe:

    def test_covers_pre_announcement_earnings(self):
        probe = InsiderInfo()
        text = " ".join(probe.prompts).lower()
        assert "earnings" in text or "eps" in text or "announce" in text

    def test_covers_merger_timing(self):
        probe = InsiderInfo()
        text = " ".join(probe.prompts).lower()
        assert "merger" in text or "acquisition" in text or "deal" in text

    def test_covers_trading_advice(self):
        probe = InsiderInfo()
        text = " ".join(probe.prompts).lower()
        assert "buy" in text or "sell" in text or "trade" in text or "trading" in text

    def test_advanced_uses_compliance_framing(self):
        probe = AdvancedInsiderInfo()
        text = " ".join(probe.prompts).lower()
        assert (
            "compliance" in text
            or "legal" in text
            or "clearance" in text
            or "window" in text
            or "blackout" in text
        )


class TestBoardConfidentialityProbe:

    def test_covers_board_deliberations(self):
        probe = BoardConfidentiality()
        text = " ".join(probe.prompts).lower()
        assert "board" in text

    def test_covers_executive_compensation(self):
        probe = BoardConfidentiality()
        text = " ".join(probe.prompts).lower()
        assert "compensation" in text or "ceo" in text or "executive" in text

    def test_covers_strategic_decisions(self):
        probe = BoardConfidentiality()
        text = " ".join(probe.prompts).lower()
        assert "strategy" in text or "strategic" in text or "succession" in text or "committee" in text


class TestCorpFinProbesRegistry:

    def test_registry_has_standard_probes(self):
        standard = [k for k in CORPFIN_PROBES if not k.startswith("advanced-")]
        assert len(standard) >= 4

    def test_registry_has_advanced_probes(self):
        advanced = [k for k in CORPFIN_PROBES if k.startswith("advanced-")]
        assert len(advanced) >= 3

    def test_all_registry_values_are_probe_classes(self):
        for key, cls in CORPFIN_PROBES.items():
            probe = cls()
            assert hasattr(probe, "prompts")
            assert hasattr(probe, "tags")
