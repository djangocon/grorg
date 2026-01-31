from __future__ import annotations

import pytest

from grants.forms import ScoreForm


@pytest.mark.django_db
class TestScoreForm:
    def test_valid_score(self):
        form = ScoreForm(data={"score": 3.0, "comment": "Good"})
        assert form.is_valid()

    def test_score_at_minimum(self):
        form = ScoreForm(data={"score": 1.0, "comment": ""})
        assert form.is_valid()

    def test_score_at_maximum(self):
        form = ScoreForm(data={"score": 5.0, "comment": ""})
        assert form.is_valid()

    def test_score_below_minimum_invalid(self):
        form = ScoreForm(data={"score": 0.0, "comment": ""})
        assert not form.is_valid()
        assert "score" in form.errors

    def test_score_above_maximum_invalid(self):
        form = ScoreForm(data={"score": 6.0, "comment": ""})
        assert not form.is_valid()
        assert "score" in form.errors

    def test_negative_score_invalid(self):
        form = ScoreForm(data={"score": -1.0, "comment": ""})
        assert not form.is_valid()
        assert "score" in form.errors

    def test_empty_score_valid(self):
        form = ScoreForm(data={"score": "", "comment": "No score yet"})
        assert form.is_valid()
