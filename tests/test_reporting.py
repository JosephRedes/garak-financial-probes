"""
Tests for report generation.
"""

from datetime import datetime

from garak_financial.judges.financial import JudgmentResult
from garak_financial.reporting import (
    AssessmentResult,
    CategoryResult,
    ReportGenerator,
    ResultAggregator,
)
from garak_financial.utils import mask_url


class TestCategoryResult:
    """Tests for CategoryResult dataclass."""

    def test_mean_score(self):
        result = CategoryResult(category="test")
        result.scores = [0.2, 0.4, 0.6, 0.8]
        assert result.mean_score == 0.5

    def test_high_concern_count(self):
        result = CategoryResult(category="test")
        result.scores = [0.2, 0.5, 0.75, 0.9, 0.95]
        assert result.high_concern_count == 3  # > 0.7

    def test_distribution(self):
        result = CategoryResult(category="test")
        result.scores = [0.1, 0.15, 0.3, 0.55, 0.85]

        dist = result.get_distribution()

        assert dist["0.0-0.2"] == 2
        assert dist["0.2-0.4"] == 1
        assert dist["0.4-0.6"] == 1
        assert dist["0.8-1.0"] == 1


class TestResultAggregator:
    """Tests for ResultAggregator class."""

    def test_add_judgment(self):
        aggregator = ResultAggregator(
            model_name="test-model",
            endpoint="http://test",
            judge_model="judge-model",
        )

        judgment = JudgmentResult(
            overall_concern=0.6,
            scores={"investment_advice": 0.7},
            reasoning="Test reasoning",
        )

        aggregator.add_judgment(
            category="impartiality",
            prompt="Should I buy Bitcoin?",
            response="Consider investing...",
            judgment=judgment,
        )

        result = aggregator.finalize()

        assert "impartiality" in result.categories
        assert result.categories["impartiality"].total_prompts == 1
        assert result.categories["impartiality"].mean_score == 0.6

    def test_high_concern_examples_limited(self):
        aggregator = ResultAggregator(
            model_name="test",
            endpoint="http://test",
            judge_model="judge",
        )

        # Add 15 high-concern judgments
        for i in range(15):
            judgment = JudgmentResult(
                overall_concern=0.8 + (i * 0.01),
                reasoning=f"Reason {i}",
            )
            aggregator.add_judgment(
                category="test",
                prompt=f"Prompt {i}",
                response=f"Response {i}",
                judgment=judgment,
            )

        result = aggregator.finalize()

        # Should be limited to 10
        assert len(result.categories["test"].high_concern_examples) == 10


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_generate_creates_markdown(self):
        result = AssessmentResult(
            model_name="test-model",
            endpoint="http://api.test.com/v1",
            assessment_date=datetime.now(),
            judge_model="gpt-4",
            total_prompts=100,
            base_prompts=50,
        )

        # Add category
        cat = CategoryResult(category="impartiality")
        cat.total_prompts = 100
        cat.scores = [0.3] * 90 + [0.8] * 10
        result.categories["impartiality"] = cat

        generator = ReportGenerator(result)
        markdown = generator.generate()

        assert "# Model Security Assessment Report" in markdown
        assert "test-model" in markdown
        assert "Investment Advice Impartiality" in markdown

    def test_endpoint_masking(self):
        masked = mask_url("http://internal.company.com/v1/chat/completions")

        assert "internal.company.com" in masked
        assert "chat/completions" not in masked

    def test_save_creates_file(self, tmp_path):
        result = AssessmentResult(
            model_name="test",
            endpoint="http://test",
            assessment_date=datetime.now(),
            judge_model="judge",
        )

        generator = ReportGenerator(result)
        filepath = generator.save(tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".md"

    def test_save_json_creates_file(self, tmp_path):
        result = AssessmentResult(
            model_name="test",
            endpoint="http://test",
            assessment_date=datetime.now(),
            judge_model="judge",
        )

        generator = ReportGenerator(result)
        filepath = generator.save_json(tmp_path)

        assert filepath.exists()
        assert filepath.suffix == ".json"


def _make_result_with_scores(mean: float = 0.3, max_score: float = 0.6) -> AssessmentResult:
    """Helper: create an AssessmentResult with one category."""
    result = AssessmentResult(
        model_name="test-model",
        endpoint="http://api.test.com/v1",
        assessment_date=datetime.now(),
        judge_model="judge-model",
        total_prompts=10,
        base_prompts=10,
    )
    cat = CategoryResult(category="impartiality")
    cat.total_prompts = 10
    n = 10
    high_n = round(max_score * n)
    low_n = n - high_n
    cat.scores = [mean] * low_n + [max_score] * high_n
    result.categories["impartiality"] = cat
    return result


class TestHTMLReportGenerator:
    """Tests for HTML report generation."""

    def test_generate_html_returns_string(self):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        html = generator.generate_html()
        assert isinstance(html, str)

    def test_generate_html_contains_model_name(self):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        html = generator.generate_html()
        assert "test-model" in html

    def test_generate_html_is_self_contained(self):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        html = generator.generate_html()
        # Should have inline CSS, no external stylesheet links
        assert "<style>" in html
        assert "<link rel=" not in html

    def test_generate_html_contains_verdict(self):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        html = generator.generate_html()
        # Verdict badge should appear somewhere
        assert any(v in html for v in ["APPROVE", "CONDITIONAL", "RECOMMEND AGAINST"])

    def test_save_html_creates_file(self, tmp_path):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        filepath = generator.save_html(tmp_path)
        assert filepath.exists()
        assert filepath.suffix == ".html"

    def test_save_html_content_is_html(self, tmp_path):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        filepath = generator.save_html(tmp_path)
        content = filepath.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content

    def test_html_escapes_model_name(self):
        result = AssessmentResult(
            model_name="<script>alert('xss')</script>",
            endpoint="http://test",
            assessment_date=datetime.now(),
            judge_model="judge",
        )
        generator = ReportGenerator(result)
        html = generator.generate_html()
        assert "<script>alert" not in html
        assert "&lt;script&gt;" in html


class TestComputeVerdict:
    """Tests for _compute_verdict thresholds."""

    def _generator_with_mean_max(self, mean: float, max_score: float) -> ReportGenerator:
        result = _make_result_with_scores(mean=mean, max_score=max_score)
        return ReportGenerator(result)

    def test_approve_verdict_low_scores(self):
        gen = self._generator_with_mean_max(mean=0.1, max_score=0.3)
        label, css_class, _ = gen._compute_verdict()
        assert label == "APPROVE"
        assert css_class == "approve"

    def test_conditional_verdict_mid_scores(self):
        gen = self._generator_with_mean_max(mean=0.35, max_score=0.55)
        label, css_class, _ = gen._compute_verdict()
        assert label == "CONDITIONAL REVIEW"
        assert css_class == "conditional"

    def test_deny_verdict_high_scores(self):
        gen = self._generator_with_mean_max(mean=0.7, max_score=0.9)
        label, css_class, _ = gen._compute_verdict()
        assert label == "RECOMMEND AGAINST"
        assert css_class == "deny"


class TestExecutiveSummary:
    """Tests for executive summary in markdown report."""

    def test_executive_summary_in_markdown(self):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        md = generator.generate()
        assert "Executive Summary" in md

    def test_executive_summary_contains_verdict(self):
        result = _make_result_with_scores()
        generator = ReportGenerator(result)
        md = generator.generate()
        assert any(v in md for v in ["APPROVE", "CONDITIONAL", "RECOMMEND AGAINST"])
