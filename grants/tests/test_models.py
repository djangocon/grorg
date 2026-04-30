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

    def test_applicants_visible_to_excludes_user_by_email(self, program, user):
        own = baker.make("grants.Applicant", program=program, email=user.email, name="Self")
        other = baker.make("grants.Applicant", program=program, email="other@example.com", name="Other")
        visible = list(program.applicants_visible_to(user))
        assert own not in visible
        assert other in visible

    def test_applicants_visible_to_does_not_exclude_by_name(self, program, user):
        """Name collisions must NOT cause other applicants to be hidden."""
        user.first_name = "Ada"
        user.last_name = "Lovelace"
        user.save()
        same_name = baker.make(
            "grants.Applicant",
            program=program,
            email="different@example.com",
            name="Ada Lovelace",
        )
        assert same_name in list(program.applicants_visible_to(user))


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


class TestQuestionFiltering:
    def test_can_filter_true_for_filterable_boolean(self, program):
        q = baker.make("grants.Question", program=program, type="boolean", filterable=True)
        assert q.can_filter() is True

    def test_can_filter_true_for_filterable_integer(self, program):
        q = baker.make("grants.Question", program=program, type="integer", filterable=True)
        assert q.can_filter() is True

    def test_can_filter_false_when_flag_off(self, program):
        q = baker.make("grants.Question", program=program, type="boolean", filterable=False)
        assert q.can_filter() is False

    def test_can_filter_false_for_text_even_if_flagged(self, program):
        q = baker.make("grants.Question", program=program, type="text", filterable=True)
        assert q.can_filter() is False

    def test_integer_filter_ranges_empty_when_no_answers(self, program):
        q = baker.make("grants.Question", program=program, type="integer", filterable=True)
        assert q.integer_filter_ranges() == []

    def test_integer_filter_ranges_single_value(self, program):
        q = baker.make("grants.Question", program=program, type="integer", filterable=True)
        applicant = baker.make("grants.Applicant", program=program, email="a@example.com")
        baker.make("grants.Answer", applicant=applicant, question=q, answer="42")
        assert q.integer_filter_ranges() == [(42, 42)]

    def test_integer_filter_ranges_returns_disjoint_buckets(self, program):
        q = baker.make("grants.Question", program=program, type="integer", filterable=True)
        for i, val in enumerate([10, 50, 100, 200, 500, 1000, 2000, 5000]):
            applicant = baker.make("grants.Applicant", program=program, email=f"a{i}@example.com")
            baker.make("grants.Answer", applicant=applicant, question=q, answer=str(val))
        ranges = q.integer_filter_ranges()
        assert ranges, "should produce buckets"
        # Buckets must be disjoint and cover min..max
        for (_, high), (next_low, _) in zip(ranges, ranges[1:]):
            assert high < next_low
        assert ranges[0][0] == 10
        assert ranges[-1][1] == 5000

    def test_integer_filter_ranges_ignores_non_numeric(self, program):
        q = baker.make("grants.Question", program=program, type="integer", filterable=True)
        a1 = baker.make("grants.Applicant", program=program, email="a1@example.com")
        a2 = baker.make("grants.Applicant", program=program, email="a2@example.com")
        baker.make("grants.Answer", applicant=a1, question=q, answer="100")
        baker.make("grants.Answer", applicant=a2, question=q, answer="not a number")
        # Should not crash and should still produce a valid range from the one parseable value
        assert q.integer_filter_ranges() == [(100, 100)]

    def test_integer_filter_ranges_empty_for_non_integer_question(self, program):
        q = baker.make("grants.Question", program=program, type="boolean", filterable=True)
        assert q.integer_filter_ranges() == []


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
