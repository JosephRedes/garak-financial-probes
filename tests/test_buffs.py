"""
Tests for financial buffs (prompt augmentation).
"""

import pytest

from garak_financial.buffs.encoding import Base64Buff, LeetSpeakBuff, ROT13Buff
from garak_financial.buffs.financial import (
    AmountVariationBuff,
    FinancialEntityBuff,
)
from garak_financial.buffs.jailbreak import JailbreakPrefixBuff, JailbreakSuffixBuff
from garak_financial.buffs.persona import PersonaVariationBuff, RolePlayBuff, UrgencyBuff


class TestEncodingBuffs:
    """Tests for encoding-based prompt augmentation."""

    def test_base64_produces_variations(self):
        """Base64 buff should produce multiple variations."""
        buff = Base64Buff()
        variations = buff.transform("Should I invest in Bitcoin?")

        assert len(variations) >= 2
        assert "Should I invest in Bitcoin?" in variations  # Original preserved

    def test_rot13_encoding(self):
        """ROT13 should correctly encode text."""
        buff = ROT13Buff()
        variations = buff.transform("test")

        assert "grfg" in variations  # ROT13 of "test"

    def test_leetspeak_substitution(self):
        """Leetspeak should substitute common characters."""
        buff = LeetSpeakBuff()
        variations = buff.transform("test")

        assert "73s7" in variations or "7357" in variations


class TestPersonaBuffs:
    """Tests for persona-based prompt augmentation."""

    def test_persona_adds_prefixes(self):
        """Persona buff should add persona prefixes."""
        buff = PersonaVariationBuff()
        variations = buff.transform("Should I invest?")

        assert len(variations) > 1
        assert any("retiree" in v for v in variations)
        assert any("advisor" in v.lower() for v in variations)

    def test_roleplay_adds_context(self):
        """Roleplay buff should add roleplay context."""
        buff = RolePlayBuff()
        variations = buff.transform("Give me stock advice")

        assert any("pretend" in v.lower() for v in variations)

    def test_urgency_adds_pressure(self):
        """Urgency buff should add time pressure context."""
        buff = UrgencyBuff()
        variations = buff.transform("Should I buy?")

        assert any("now" in v.lower() or "fast" in v.lower() for v in variations)


class TestFinancialBuffs:
    """Tests for financial entity swapping."""

    def test_ticker_swap(self):
        """Should swap ticker symbols."""
        buff = FinancialEntityBuff()
        variations = buff.transform("Should I buy AAPL?")

        assert len(variations) >= 2
        assert any("TSLA" in v or "NVDA" in v for v in variations)

    def test_crypto_swap(self):
        """Should swap cryptocurrency names."""
        buff = FinancialEntityBuff()
        variations = buff.transform("Should I invest in Bitcoin?")

        assert any("Ethereum" in v for v in variations)

    def test_amount_variations(self):
        """Should add amount context."""
        buff = AmountVariationBuff()
        variations = buff.transform("Should I invest?")

        # Should add amount context when none present
        assert any("$" in v or "savings" in v for v in variations)


class TestJailbreakBuffs:
    """Tests for jailbreak augmentations."""

    def test_prefix_jailbreaks(self):
        """Should add jailbreak prefixes."""
        buff = JailbreakPrefixBuff()
        variations = buff.transform("Give me advice")

        assert any("ignore" in v.lower() for v in variations)
        assert any("pretend" in v.lower() for v in variations)

    def test_suffix_jailbreaks(self):
        """Should add jailbreak suffixes."""
        buff = JailbreakSuffixBuff()
        variations = buff.transform("Give me advice")

        assert any("without" in v.lower() or "direct" in v.lower() for v in variations)


class TestBuffMultiplication:
    """Test that buffs multiply prompts as expected."""

    def test_combined_multiplication(self):
        """Multiple buffs should significantly multiply prompts."""
        prompt = "Should I invest in Bitcoin?"
        total_variations = set()

        buffs = [
            Base64Buff(),
            PersonaVariationBuff(),
            FinancialEntityBuff(),
        ]

        for buff in buffs:
            for variation in buff.transform(prompt):
                total_variations.add(variation)

        # Should have many unique variations
        assert len(total_variations) > 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
