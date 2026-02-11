"""
Financial services buffs (prompt augmentations) for Garak.

Buffs transform base prompts into variations to test robustness
of model guardrails against evasion techniques.
"""

from garak_financial.buffs.encoding import Base64Buff, LeetSpeakBuff, ROT13Buff
from garak_financial.buffs.financial import AmountVariationBuff, FinancialEntityBuff
from garak_financial.buffs.jailbreak import JailbreakPrefixBuff
from garak_financial.buffs.persona import PersonaVariationBuff

__all__ = [
    "Base64Buff",
    "ROT13Buff",
    "LeetSpeakBuff",
    "PersonaVariationBuff",
    "FinancialEntityBuff",
    "AmountVariationBuff",
    "JailbreakPrefixBuff",
]
