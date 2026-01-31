from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from grants.models import Score


class TestProgramModel:
    def test_str_returns_name(self, program):
        assert str(program) == "Test Program"

    def test_user_allowed_returns_true_for_member(self, program, user):
        assert program.user_allowed(user) is True

    def test_user_allowed_returns_false_for_non_member(self, program, other_user):
        assert program.user_allowed(other_user) is False

    def test_urls_view(self, program):
        assert program.urls.view == "/test-program/"

    def test_urls_apply(self, program):
        assert program.urls.apply == "/test-program/apply/"


class TestQuestionModel:
    def test_str_returns_question_text(self, question):
        assert str(question) == "Why do you want this grant?"

    def test_can_delete_when_no_answers(self, question):
        assert question.can_delete() is True

    def test_cannot_delete_when_has_answers(self, question, applicant):
        baker.make(
            "grants.Answer",
            applicant=applicant,
            question=question,
            answer="I need funding for travel",
        )
        assert question.can_delete() is False


class TestApplicantModel:
    def test_str_returns_name(self, applicant):
        assert str(applicant) == "Test Applicant"

    def test_average_score_with_no_scores(self, applicant):
        assert applicant.average_score() is None

    def test_average_score_with_one_score(self, applicant, user):
        baker.make("grants.Score", applicant=applicant, user=user, score=4.0)
        assert applicant.average_score() == 4.0

    def test_average_score_with_multiple_scores(self, applicant, user, other_user):
        baker.make("grants.Score", applicant=applicant, user=user, score=3.0)
        baker.make("grants.Score", applicant=applicant, user=other_user, score=5.0)
        assert applicant.average_score() == 4.0

    def test_variance_with_no_scores(self, applicant):
        assert applicant.variance() == 0

    def test_variance_with_one_score(self, applicant, user):
        baker.make("grants.Score", applicant=applicant, user=user, score=4.0)
        assert applicant.variance() == 0

    def test_stdev_returns_sqrt_of_variance(self, applicant, user, other_user):
        baker.make("grants.Score", applicant=applicant, user=user, score=2.0)
        baker.make("grants.Score", applicant=applicant, user=other_user, score=4.0)
        variance = applicant.variance()
        assert applicant.stdev() == variance**0.5


class TestScoreModel:
    def test_score_history_human_formats_correctly(self, score):
        score.score_history = "3.0,4.0,5.0"
        assert score.score_history_human() == "3.0, 4.0, 5.0"

    def test_score_history_human_handles_empty(self, score):
        score.score_history = None
        assert score.score_history_human() == ""


class TestScoreValidation:
    def test_score_accepts_valid_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=3.0)
        score.full_clean()

    def test_score_accepts_minimum_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=1.0)
        score.full_clean()

    def test_score_accepts_maximum_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=5.0)
        score.full_clean()

    def test_score_accepts_null_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=None)
        score.full_clean()

    def test_score_rejects_value_below_minimum(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=0.5)
        with pytest.raises(ValidationError):
            score.full_clean()

    def test_score_rejects_negative_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=-2.0)
        with pytest.raises(ValidationError):
            score.full_clean()

    def test_score_rejects_value_above_maximum(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=6.0)
        with pytest.raises(ValidationError):
            score.full_clean()


class TestResourceModel:
    def test_str_returns_name(self, resource):
        assert str(resource) == "Travel Grant"

    def test_fa_icon_returns_correct_icon(self, resource):
        assert resource.fa_icon() == "money"

    def test_amount_allocated_with_no_allocations(self, resource):
        assert resource.amount_allocated() == 0

    def test_amount_remaining_with_no_allocations(self, resource):
        assert resource.amount_remaining() == 1000

    def test_amount_allocated_with_allocations(self, resource, applicant):
        baker.make(
            "grants.Allocation",
            applicant=applicant,
            resource=resource,
            amount=300,
        )
        assert resource.amount_allocated() == 300
        assert resource.amount_remaining() == 700
