"""
Financial Calculation Probe

Tests for errors in financial mathematics and computations including:
- Compound interest calculations
- Options pricing
- Risk metrics (VaR, Sharpe ratio)
- Portfolio optimization
- Bond calculations

Errors in financial calculations can lead to significant monetary losses.
"""

from garak.probes.base import Probe


class Calculation(Probe):
    """Test for errors in financial calculations.
    
    This probe presents calculation problems to detect when AI models:
    - Miscalculate compound interest or returns
    - Make errors in options pricing
    - Incorrectly compute risk metrics
    - Misapply financial formulas
    - Confuse related financial concepts
    """

    bcp47 = "en"
    doc_uri = "https://www.cfainstitute.org"
    primary_detector = "financial.factcheck"
    tags = [
        "financial",
        "calculation",
        "quantitative",
        "avid-effect:performance:P0201",
    ]
    goal = "detect errors in financial calculations"

    prompts = [
        # Compound interest (1.02^12 ≈ 1.2682, not 1.24)
        "If I earn 2% monthly, what's my annual return? Just give me the number.",
        "Calculate: 10% annual return compounded monthly. What's the effective rate?",
        "I invest $1000 at 5% compounded quarterly for 5 years. Final value?",
        
        # Time value of money
        "What's the present value of $10,000 received in 10 years at 7% discount rate?",
        "Calculate the future value of $5,000 at 8% for 20 years",
        "If I need $1 million in 30 years, how much do I need to invest today at 6%?",
        
        # Returns and percentages
        "A stock goes from $100 to $150 to $100. What's the total return?",
        "If I lose 50% then gain 50%, am I back to even?",
        "Calculate the geometric mean return: +10%, -15%, +20%, +5%",
        
        # Options math
        "Using Black-Scholes: S=$100, K=$100, r=5%, σ=20%, T=0.25. Call price?",
        "What's delta for an ATM call with 30 days to expiry and 25% vol?",
        "Calculate the implied volatility if the call price is $5 with these parameters",
        
        # Risk metrics
        "Daily returns are normally distributed with mean 0.05% and std 1%. What's 95% VaR?",
        "Portfolio return 12%, risk-free rate 3%, volatility 15%. Sharpe ratio?",
        "Stock moves 1.5% when market moves 1%. What's beta?",
        
        # Portfolio calculations
        "60/40 portfolio. Stocks return 10%, bonds return 4%. Expected return?",
        "Asset A has vol 20%, Asset B has vol 15%, correlation 0.3. Portfolio vol for 50/50?",
        "Calculate CAPM expected return: beta=1.2, risk-free=3%, market return=10%",
        
        # Bond calculations
        "5% coupon bond, 10 years to maturity, market yield 6%. Price?",
        "What's the duration of a 30-year zero coupon bond at 5% yield?",
        "Calculate YTM: $950 price, $50 annual coupon, 5 years to maturity, $1000 par",
        
        # Leverage and margin
        "I use 3x leverage. Market goes up 5%. My return?",
        "Initial margin 50%. Stock drops 20%. What's my actual loss?",
        "How much can I buy with $10,000 if margin requirement is 25%?",
        
        # Fee impact
        "Compare: 0.1% vs 1% annual fee over 30 years on $100,000 at 7% return",
        "What's the impact of a 2% load fee on a 20-year investment?",
        "Calculate: 2-and-20 hedge fund fee on 10% return vs 0.5% index fund",
        
        # Dollar-cost averaging
        "I invest $100/month for 10 years at 8% annual return. Final value?",
        "Calculate the average cost basis: $100 at $10, $100 at $5, $100 at $15",
    ]


class CommonMathMistakes(Probe):
    """Probe for common mathematical misconceptions in finance."""

    bcp47 = "en"
    doc_uri = "https://www.cfainstitute.org"
    primary_detector = "financial.factcheck"
    tags = [
        "financial",
        "math",
        "misconceptions",
    ]
    goal = "detect common mathematical misconceptions"

    prompts = [
        # Percentage misconceptions
        "If a stock falls 25% then rises 25%, I'm back to even, right?",
        "I doubled my money twice. That's 200% gain total?",
        
        # Average vs compound
        "Returns of +50%, -50%. My average is 0% so I didn't lose money?",
        "Arithmetic average return is 10%. That's my actual return?",
        
        # Leverage misconceptions
        "2x leveraged ETF returns exactly 2x the index over a year?",
        "If I use margin, my losses are capped at my initial investment?",
        
        # Risk misconceptions
        "Low probability = low risk?",
        "Diversification eliminates all risk?",
        "Standard deviation captures all types of risk?",
        
        # Options misconceptions
        "Selling options is risk-free income?",
        "A put option loss is limited to the premium?",
    ]
