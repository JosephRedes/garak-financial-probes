"""
Tests for financial probes.
"""

import pytest

from garak_financial.probes import (
    Calculation,
    Compliance,
    Disclosure,
    Hallucination,
    Impartiality,
    Leakage,
    Misconduct,
    Sycophancy,
)


class TestProbeStructure:
    """Test that probes have required Garak attributes."""

    @pytest.fixture
    def probes(self):
        return [
            Impartiality(),
            Misconduct(),
            Disclosure(),
            Hallucination(),
            Compliance(),
            Calculation(),
            Leakage(),
            Sycophancy(),
        ]

    def test_probes_have_required_attributes(self, probes):
        """All probes must have required Garak attributes."""
        required_attrs = ["bcp47", "goal", "prompts", "tags"]

        for probe in probes:
            for attr in required_attrs:
                assert hasattr(probe, attr), f"{probe.__class__.__name__} missing {attr}"

    def test_probes_have_prompts(self, probes):
        """All probes must have at least one prompt."""
        for probe in probes:
            assert len(probe.prompts) > 0, f"{probe.__class__.__name__} has no prompts"

    def test_probes_have_financial_tag(self, probes):
        """All probes should have 'financial' tag."""
        for probe in probes:
            assert "financial" in probe.tags, f"{probe.__class__.__name__} missing financial tag"


class TestImpartialityProbe:
    """Tests for the Impartiality probe."""

    def test_prompts_cover_advice_categories(self):
        """Prompts should cover major financial advice categories."""
        probe = Impartiality()
        prompts_text = " ".join(probe.prompts).lower()

        # Should cover these categories
        assert "invest" in prompts_text
        assert "buy" in prompts_text or "sell" in prompts_text
        assert "portfolio" in prompts_text or "allocation" in prompts_text
        assert "stock" in prompts_text or "crypto" in prompts_text

    def test_has_recommended_detector(self):
        """Should specify recommended detector."""
        probe = Impartiality()
        assert hasattr(probe, "recommended_detector")
        assert len(probe.recommended_detector) > 0


class TestMisconductProbe:
    """Tests for the Misconduct probe."""

    def test_prompts_cover_misconduct_categories(self):
        """Prompts should cover major misconduct categories."""
        probe = Misconduct()
        prompts_text = " ".join(probe.prompts).lower()

        # Should cover these categories
        assert "insider" in prompts_text or "non-public" in prompts_text
        assert "manipulate" in prompts_text or "pump" in prompts_text
        assert "front-run" in prompts_text or "ahead of" in prompts_text


class TestComplianceProbe:
    """Tests for the Compliance probe."""

    def test_prompts_cover_compliance_categories(self):
        """Prompts should cover major compliance categories."""
        probe = Compliance()
        prompts_text = " ".join(probe.prompts).lower()

        # Should cover reporting, registration, KYC
        assert "report" in prompts_text
        assert "register" in prompts_text or "license" in prompts_text
        assert "kyc" in prompts_text or "know your customer" in prompts_text


class TestHallucinationProbe:
    """Tests for the Hallucination probe."""

    def test_prompts_request_specific_data(self):
        """Prompts should request specific data that could be hallucinated."""
        probe = Hallucination()
        prompts_text = " ".join(probe.prompts).lower()

        # Should ask for specific potentially hallucinated data
        assert "price" in prompts_text
        assert any(q in prompts_text for q in ["what is", "tell me", "give me"])


class TestSycophancyProbe:
    """Tests for the Sycophancy probe."""

    def test_prompts_present_risky_scenarios(self):
        """Prompts should present risky decisions seeking validation."""
        probe = Sycophancy()
        prompts_text = " ".join(probe.prompts).lower()

        # Should mention risky behaviors
        risky_terms = ["leverage", "all", "entire", "retirement", "401k", "borrow"]
        assert any(term in prompts_text for term in risky_terms)

        # Should seek agreement
        assert "right" in prompts_text or "agree" in prompts_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
