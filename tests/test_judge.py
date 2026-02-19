"""
Tests for LLM-as-Judge system.
"""

from unittest.mock import Mock

import pytest

from garak_financial.judges import (
    FINANCIAL_JUDGE_PROMPT,
    FINANCIAL_JUDGE_SYSTEM,
    HALLUCINATION_JUDGE,
    INVESTMENT_ADVICE_JUDGE,
    MISCONDUCT_JUDGE,
)
from garak_financial.judges.financial import (
    FinancialJudge,
    HybridJudge,
    JudgmentResult,
)


class TestJudgmentResult:
    """Tests for JudgmentResult dataclass."""

    def test_max_score(self):
        result = JudgmentResult(
            scores={
                "investment_advice": 0.3,
                "price_prediction": 0.8,
                "confidentiality": 0.1,
            }
        )
        assert result.max_score == 0.8

    def test_mean_score(self):
        result = JudgmentResult(
            scores={
                "investment_advice": 0.3,
                "price_prediction": 0.6,
                "confidentiality": 0.3,
            }
        )
        assert result.mean_score == pytest.approx(0.4)

    def test_empty_scores_uses_overall(self):
        result = JudgmentResult(overall_concern=0.7)
        assert result.max_score == 0.7
        assert result.mean_score == 0.7


class TestFinancialJudge:
    """Tests for FinancialJudge class."""

    def test_sanitize_input_truncates_long_text(self):
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        long_text = "x" * 20000
        sanitized = judge._sanitize_input(long_text)

        assert len(sanitized) < 15000
        assert "truncated" in sanitized

    def test_parse_judgment_valid_json(self):
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        json_response = '''
        {
            "scores": {
                "investment_advice": 0.8,
                "price_prediction": 0.2
            },
            "overall_concern": 0.6,
            "reasoning": "Provides specific allocation",
            "key_phrases": ["recommend buying"]
        }
        '''

        result = judge._parse_judgment(json_response)

        assert result.scores["investment_advice"] == 0.8
        assert result.overall_concern == 0.6
        assert "allocation" in result.reasoning

    def test_parse_judgment_invalid_json_fallback(self):
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        invalid_response = "The score is 0.75 for this response"
        result = judge._parse_judgment(invalid_response)

        assert result.overall_concern == 0.75

    def test_score_validation_clamps_values(self):
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        json_response = '''
        {
            "scores": {"test": 1.5},
            "overall_concern": -0.3
        }
        '''

        result = judge._parse_judgment(json_response)

        assert result.scores["test"] == 1.0  # Clamped to max
        assert result.overall_concern == 0.0  # -0.3 clamps to 0.0 via max(0.0, ...)


class TestHybridJudge:
    """Tests for HybridJudge class."""

    def test_high_regex_score_skips_llm(self):
        llm_judge = Mock()
        regex_detector = Mock()
        regex_detector.detect.return_value = [0.95]

        hybrid = HybridJudge(llm_judge=llm_judge, regex_detector=regex_detector)
        result = hybrid.evaluate("prompt", "I recommend buying AAPL")

        assert result.overall_concern == 0.95
        llm_judge.evaluate.assert_not_called()

    def test_low_regex_score_skips_llm(self):
        llm_judge = Mock()
        regex_detector = Mock()
        regex_detector.detect.return_value = [0.05]

        hybrid = HybridJudge(llm_judge=llm_judge, regex_detector=regex_detector)
        result = hybrid.evaluate("prompt", "I cannot provide financial advice")

        assert result.overall_concern == 0.05
        llm_judge.evaluate.assert_not_called()

    def test_middle_regex_score_uses_llm(self):
        llm_judge = Mock()
        llm_judge.evaluate.return_value = JudgmentResult(overall_concern=0.65)
        regex_detector = Mock()
        regex_detector.detect.return_value = [0.5]

        hybrid = HybridJudge(llm_judge=llm_judge, regex_detector=regex_detector)
        result = hybrid.evaluate("prompt", "Consider diversifying your portfolio")

        llm_judge.evaluate.assert_called_once()
        assert result.overall_concern == 0.65

    def test_force_llm_bypasses_regex(self):
        llm_judge = Mock()
        llm_judge.evaluate.return_value = JudgmentResult(overall_concern=0.7)
        regex_detector = Mock()
        regex_detector.detect.return_value = [0.05]  # Would skip LLM normally

        hybrid = HybridJudge(llm_judge=llm_judge, regex_detector=regex_detector)
        hybrid.evaluate("prompt", "response", force_llm=True)

        llm_judge.evaluate.assert_called_once()


class TestJudgePrompts:
    """Tests for judge prompt templates."""

    def test_financial_judge_prompt_has_placeholders(self):
        assert "{prompt}" in FINANCIAL_JUDGE_PROMPT
        assert "{response}" in FINANCIAL_JUDGE_PROMPT

    def test_financial_judge_prompt_requests_json(self):
        assert "JSON" in FINANCIAL_JUDGE_PROMPT or "json" in FINANCIAL_JUDGE_PROMPT

    def test_system_prompt_establishes_role(self):
        assert "compliance" in FINANCIAL_JUDGE_SYSTEM.lower()
        assert "expert" in FINANCIAL_JUDGE_SYSTEM.lower()

    def test_investment_advice_judge_has_scores_key(self):
        """Category judge must emit scores dict so _parse_judgment can read it."""
        assert '"scores"' in INVESTMENT_ADVICE_JUDGE

    def test_investment_advice_judge_has_overall_concern_key(self):
        assert '"overall_concern"' in INVESTMENT_ADVICE_JUDGE

    def test_misconduct_judge_has_scores_key(self):
        assert '"scores"' in MISCONDUCT_JUDGE

    def test_hallucination_judge_has_scores_key(self):
        assert '"scores"' in HALLUCINATION_JUDGE

    def test_parse_judgment_category_judge_schema(self):
        """Regression: category judge JSON must parse with non-zero overall_concern."""
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        # Simulate what INVESTMENT_ADVICE_JUDGE now returns
        json_response = """{
            "scores": {
                "investment_advice": 0.9,
                "price_prediction": 0.3,
                "confidentiality": 0.0,
                "regulatory_concern": 0.2,
                "factual_accuracy": 0.4,
                "sycophancy": 0.5
            },
            "overall_concern": 0.7,
            "reasoning": "Provides specific buy recommendation",
            "key_phrases": ["I recommend buying"],
            "provides_recommendation": true,
            "mentions_specific_securities": true,
            "includes_disclaimer": false,
            "evidence": ["I recommend buying AAPL"]
        }"""
        result = judge._parse_judgment(json_response)
        assert result.scores["investment_advice"] == 0.9
        assert result.overall_concern == 0.7
        # Guard against the old silent-zero bug
        assert result.overall_concern > 0.0


class TestExtractFromText:
    """Tests for the _extract_from_text fallback."""

    def test_ignores_bare_integers(self):
        """Bare 0 and 1 in prose must not be treated as scores."""
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        text = "I found 1 key issue and 0 disclaimers. The concern is 0.85."
        result = judge._extract_from_text(text)
        # Should only find 0.85, not 1 or 0
        assert result.overall_concern == pytest.approx(0.85)

    def test_averages_multiple_scores(self):
        """Multiple decimal scores should be averaged."""
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        text = "investment_advice=0.8 sycophancy=0.6"
        result = judge._extract_from_text(text)
        assert result.overall_concern == pytest.approx(0.7)

    def test_defaults_to_half_when_no_floats(self):
        """When no decimal score found, default to 0.5."""
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        text = "The model provided educational content without specific advice."
        result = judge._extract_from_text(text)
        assert result.overall_concern == 0.5

    def test_parse_judgment_invalid_json_no_integer_grab(self):
        """Regression: non-JSON with only integers must not return 1.0."""
        client = Mock()
        judge = FinancialJudge(client=client, model="test")

        # Old bug: "1 key issue" → grabs bare 1 → returns 1.0
        invalid_response = "There is 1 key issue: the response recommends a specific stock."
        result = judge._parse_judgment(invalid_response)
        assert result.overall_concern != 1.0
        assert result.overall_concern == 0.5  # no decimal floats → default
