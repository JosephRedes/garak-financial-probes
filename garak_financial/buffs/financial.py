"""
Financial Entity Variation Buffs

Transform prompts by swapping financial entities (tickers, amounts,
asset classes) to test consistency of model behavior.
"""

import re
from typing import List


class BaseBuff:
    """Base class for prompt transformation buffs."""

    def transform(self, prompt: str) -> List[str]:
        raise NotImplementedError


class FinancialEntityBuff(BaseBuff):
    """Swap financial entities in prompts.

    Tests if model behavior is consistent across different
    securities, companies, and asset classes.
    """

    name = "financial_entity"
    description = "Swap tickers, companies, and asset classes"

    # Common ticker symbols to swap
    TICKERS = ["AAPL", "TSLA", "NVDA", "GOOGL", "MSFT", "AMZN", "META", "AMD"]

    # Cryptocurrency names
    CRYPTOS = ["Bitcoin", "Ethereum", "Dogecoin", "Solana", "XRP", "Cardano"]

    # Asset classes
    ASSET_CLASSES = [
        ("stocks", "bonds"),
        ("stocks", "real estate"),
        ("stocks", "crypto"),
        ("crypto", "gold"),
        ("ETFs", "mutual funds"),
    ]

    # Companies (for non-ticker references)
    COMPANIES = ["Apple", "Tesla", "Google", "Amazon", "Microsoft", "Meta", "Netflix"]

    def transform(self, prompt: str) -> List[str]:
        variations = [prompt]
        prompt_lower = prompt.lower()

        # Swap crypto names
        for crypto in self.CRYPTOS:
            if crypto.lower() in prompt_lower:
                for replacement in self.CRYPTOS:
                    if replacement != crypto:
                        new_prompt = re.sub(
                            crypto, replacement, prompt, flags=re.IGNORECASE
                        )
                        if new_prompt != prompt:
                            variations.append(new_prompt)
                            break  # Just one swap per crypto

        # Swap tickers
        for ticker in self.TICKERS:
            if ticker in prompt:
                for replacement in self.TICKERS:
                    if replacement != ticker:
                        variations.append(prompt.replace(ticker, replacement))
                        break

        # Swap company names
        for company in self.COMPANIES:
            if company.lower() in prompt_lower:
                for replacement in self.COMPANIES:
                    if replacement != company:
                        new_prompt = re.sub(
                            company, replacement, prompt, flags=re.IGNORECASE
                        )
                        if new_prompt != prompt:
                            variations.append(new_prompt)
                            break

        return variations


class AmountVariationBuff(BaseBuff):
    """Vary monetary amounts in prompts.

    Tests if model behavior changes based on investment size.
    Models might be more cautious with larger amounts.
    """

    name = "amount_variation"
    description = "Vary monetary amounts in prompts"

    AMOUNTS = [
        ("$1,000", "$100"),
        ("$1,000", "$10,000"),
        ("$1,000", "$100,000"),
        ("$1,000", "$1,000,000"),
        ("$1,000", "my life savings"),
        ("$1,000", "my retirement fund"),
        ("$1,000", "money I can't afford to lose"),
    ]

    PERCENTAGE_VARIATIONS = [
        ("10%", "1%"),
        ("10%", "50%"),
        ("10%", "100%"),
        ("10%", "all"),
    ]

    def transform(self, prompt: str) -> List[str]:
        variations = [prompt]

        # Look for dollar amounts and swap
        dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
        if re.search(dollar_pattern, prompt):
            for original, replacement in self.AMOUNTS:
                if original.replace(",", "") in prompt.replace(",", ""):
                    variations.append(prompt.replace(original, replacement))

        # Look for percentages and swap
        if "%" in prompt:
            for original, replacement in self.PERCENTAGE_VARIATIONS:
                if original in prompt:
                    variations.append(prompt.replace(original, replacement))

        # Add amount context if none present
        if not re.search(dollar_pattern, prompt):
            variations.append(f"I have $10,000 to invest. {prompt}")
            variations.append(f"This is about my retirement savings. {prompt}")

        return variations


class TimeframeVariationBuff(BaseBuff):
    """Vary investment timeframes in prompts.

    Tests if model adjusts advice appropriately for different
    investment horizons.
    """

    name = "timeframe_variation"
    description = "Vary investment timeframes"

    TIMEFRAMES = [
        "for the next week",
        "for the next month",
        "for one year",
        "for 5 years",
        "for retirement in 30 years",
        "for my child's college in 10 years",
        "day trading today",
    ]

    def transform(self, prompt: str) -> List[str]:
        variations = [prompt]

        for timeframe in self.TIMEFRAMES:
            variations.append(f"{prompt} {timeframe}")

        return variations
