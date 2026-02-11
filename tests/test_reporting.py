"""
Tests for report generation.
"""

import pytest
from datetime import datetime
from pathlib import Path
from garak_financial.reporting import (
    CategoryResult,
    AssessmentResult,
    ResultAggregator,
    ReportGenerator,
)
from garak_financial.judges.financial import JudgmentResult


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
        result = AssessmentResult(
            model_name="test",
            endpoint="http://internal.company.com/v1/chat/completions",
            assessment_date=datetime.now(),
            judge_model="judge",
        )
        
        generator = ReportGenerator(result)
        masked = generator._mask_endpoint(result.endpoint)
        
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
