from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from model_bakery import baker

from grants.forms import ScoreForm
from grants.models import Applicant, Question, Score


# =============================================================================
# Model Tests
# =============================================================================


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


# =============================================================================
# Score Validation Tests
# =============================================================================


class TestScoreValidation:
    def test_score_accepts_valid_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=3.0)
        score.full_clean()  # Should not raise

    def test_score_accepts_minimum_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=1.0)
        score.full_clean()  # Should not raise

    def test_score_accepts_maximum_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=5.0)
        score.full_clean()  # Should not raise

    def test_score_accepts_null_value(self, applicant, user):
        score = Score(applicant=applicant, user=user, score=None)
        score.full_clean()  # Should not raise

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


# =============================================================================
# Form Tests
# =============================================================================


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


# =============================================================================
# View Tests
# =============================================================================


class TestIndexView:
    def test_homepage_returns_200(self, client, db):
        response = client.get("/")
        assert response.status_code == 200


class TestProgramHomeView:
    def test_requires_authentication(self, client, program):
        response = client.get(f"/{program.slug}/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_requires_program_access(self, client, program, other_user):
        client.force_login(other_user)
        response = client.get(f"/{program.slug}/")
        assert response.status_code == 404

    def test_accessible_to_program_member(self, client_logged_in, program):
        response = client_logged_in.get(f"/{program.slug}/")
        assert response.status_code == 200


class TestProgramApplyView:
    def test_apply_page_accessible_without_login(self, client, program):
        response = client.get(f"/{program.slug}/apply/")
        assert response.status_code == 200

    def test_apply_creates_applicant(self, client, program, question):
        response = client.post(
            f"/{program.slug}/apply/",
            {
                "name": "New Applicant",
                "email": "new@example.com",
                f"question-{question.id}": "I need this grant",
            },
        )
        assert response.status_code == 302
        assert Applicant.objects.filter(email="new@example.com").exists()

    def test_apply_rejects_duplicate_email(self, client, program, question, applicant):
        response = client.post(
            f"/{program.slug}/apply/",
            {
                "name": "Another Applicant",
                "email": applicant.email,
                f"question-{question.id}": "I also need this grant",
            },
        )
        assert response.status_code == 200  # Form re-displayed with errors
        assert Applicant.objects.filter(email=applicant.email).count() == 1


class TestProgramApplicantsView:
    def test_requires_authentication(self, client, program):
        response = client.get(f"/{program.slug}/applicants/")
        assert response.status_code == 302

    def test_lists_applicants(self, client_logged_in, program, applicant):
        response = client_logged_in.get(f"/{program.slug}/applicants/")
        assert response.status_code == 200
        assert applicant.name in response.content.decode()


class TestApplicantViewAndScoring:
    def test_view_applicant(self, client_logged_in, program, applicant):
        response = client_logged_in.get(f"/{program.slug}/applicants/{applicant.id}/")
        assert response.status_code == 200

    def test_submit_score(self, client_logged_in, program, applicant, user):
        response = client_logged_in.post(
            f"/{program.slug}/applicants/{applicant.id}/",
            {"score": 4.0, "comment": "Great application"},
        )
        assert response.status_code == 302
        score = Score.objects.get(applicant=applicant, user=user)
        assert score.score == 4.0
        assert score.comment == "Great application"

    def test_update_score_tracks_history(self, client_logged_in, program, applicant, user):
        baker.make("grants.Score", applicant=applicant, user=user, score=3.0)
        client_logged_in.post(
            f"/{program.slug}/applicants/{applicant.id}/",
            {"score": 5.0, "comment": "Changed my mind"},
        )
        score = Score.objects.get(applicant=applicant, user=user)
        assert score.score == 5.0
        assert "3.0" in score.score_history


class TestProgramQuestionsView:
    def test_requires_authentication(self, client, program):
        response = client.get(f"/{program.slug}/questions/")
        assert response.status_code == 302

    def test_lists_questions(self, client_logged_in, program, question):
        response = client_logged_in.get(f"/{program.slug}/questions/")
        assert response.status_code == 200
        assert question.question in response.content.decode()


class TestProgramResourcesView:
    def test_requires_authentication(self, client, program):
        response = client.get(f"/{program.slug}/resources/")
        assert response.status_code == 302

    def test_lists_resources(self, client_logged_in, program, resource):
        response = client_logged_in.get(f"/{program.slug}/resources/")
        assert response.status_code == 200
        assert resource.name in response.content.decode()
