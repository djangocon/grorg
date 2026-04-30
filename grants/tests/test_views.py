from __future__ import annotations

import pytest
from model_bakery import baker

from grants.models import Applicant, Program, Score


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


class TestProgramApplicantsFilters:
    """Filter UI is only shown to managers; make user the program manager."""

    @pytest.fixture
    def manager_client(self, client_logged_in, program, user):
        program.created_by = user
        program.save()
        return client_logged_in

    def test_filterable_boolean_question_appears_in_filter_ui(self, manager_client, program):
        baker.make(
            "grants.Question",
            program=program,
            type="boolean",
            question="Is this your first time?",
            filterable=True,
        )
        response = manager_client.get(f"/{program.slug}/applicants/")
        body = response.content.decode()
        assert "Filter by Question" in body
        assert "Is this your first time?" in body

    def test_non_filterable_boolean_question_hidden_from_filter_ui(self, manager_client, program):
        baker.make(
            "grants.Question",
            program=program,
            type="boolean",
            question="Some private flag",
            filterable=False,
        )
        response = manager_client.get(f"/{program.slug}/applicants/")
        assert "Filter by Question" not in response.content.decode()

    def test_boolean_yes_filter_filters_applicants(self, manager_client, program):
        q = baker.make("grants.Question", program=program, type="boolean", filterable=True)
        yes_applicant = baker.make("grants.Applicant", program=program, name="YesPerson", email="yes@example.com")
        no_applicant = baker.make("grants.Applicant", program=program, name="NoPerson", email="no@example.com")
        baker.make("grants.Answer", applicant=yes_applicant, question=q, answer="True")
        baker.make("grants.Answer", applicant=no_applicant, question=q, answer="False")
        response = manager_client.get(f"/{program.slug}/applicants/?q{q.id}=yes")
        body = response.content.decode()
        assert "YesPerson" in body
        assert "NoPerson" not in body

    def test_integer_question_shows_range_buttons(self, manager_client, program):
        q = baker.make("grants.Question", program=program, type="integer", filterable=True, question="Years experience")
        for i, val in enumerate([1, 5, 10, 20]):
            a = baker.make("grants.Applicant", program=program, email=f"a{i}@example.com")
            baker.make("grants.Answer", applicant=a, question=q, answer=str(val))
        response = manager_client.get(f"/{program.slug}/applicants/")
        body = response.content.decode()
        assert "Years experience" in body
        # At least one range button exists with low-high href format
        assert f"q{q.id}=1-" in body or f"q{q.id}=" in body

    def test_integer_range_filter_filters_applicants(self, manager_client, program):
        q = baker.make("grants.Question", program=program, type="integer", filterable=True)
        small = baker.make("grants.Applicant", program=program, name="SmallBudget", email="s@example.com")
        large = baker.make("grants.Applicant", program=program, name="LargeBudget", email="l@example.com")
        baker.make("grants.Answer", applicant=small, question=q, answer="100")
        baker.make("grants.Answer", applicant=large, question=q, answer="5000")
        response = manager_client.get(f"/{program.slug}/applicants/?q{q.id}=0-1000")
        body = response.content.decode()
        assert "SmallBudget" in body
        assert "LargeBudget" not in body

    def test_active_filter_link_clears_itself(self, manager_client, program):
        """Clicking the currently-active filter option should produce a URL
        that omits its query param (toggle off)."""
        q = baker.make("grants.Question", program=program, type="boolean", filterable=True)
        response = manager_client.get(f"/{program.slug}/applicants/?q{q.id}=yes")
        body = response.content.decode()
        # The "Yes" link must not point back to ?q{id}=yes when yes is active.
        assert f'href="?q{q.id}=yes"' not in body
        # The "No" link should still point to ?q{id}=no.
        assert f'href="?q{q.id}=no"' in body

    def test_filter_does_not_apply_for_non_managers(self, client_logged_in, program):
        """Non-managers should not be able to use filters even if URL has them."""
        q = baker.make("grants.Question", program=program, type="boolean", filterable=True)
        yes_applicant = baker.make("grants.Applicant", program=program, name="YesPerson", email="yes@example.com")
        no_applicant = baker.make("grants.Applicant", program=program, name="NoPerson", email="no@example.com")
        baker.make("grants.Answer", applicant=yes_applicant, question=q, answer="True")
        baker.make("grants.Answer", applicant=no_applicant, question=q, answer="False")
        response = client_logged_in.get(f"/{program.slug}/applicants/?q{q.id}=yes")
        body = response.content.decode()
        # Filter should be ignored — both applicants visible
        assert "YesPerson" in body
        assert "NoPerson" in body


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


class TestOwnApplicationHiddenFromReviewer:
    """A user who also applied must never see their own application."""

    def test_list_excludes_own_application(self, client_logged_in, program, user):
        own = baker.make("grants.Applicant", program=program, email=user.email, name="Self")
        other = baker.make("grants.Applicant", program=program, email="o@example.com", name="Other")
        response = client_logged_in.get(f"/{program.slug}/applicants/")
        body = response.content.decode()
        assert other.name in body
        assert own.name not in body

    def test_detail_returns_404_for_own_application(self, client_logged_in, program, user):
        own = baker.make("grants.Applicant", program=program, email=user.email, name="Self")
        response = client_logged_in.get(f"/{program.slug}/applicants/{own.id}/")
        assert response.status_code == 404

    def test_allocations_returns_404_for_own_application(self, client_logged_in, program, user):
        own = baker.make("grants.Applicant", program=program, email=user.email, name="Self")
        response = client_logged_in.get(f"/{program.slug}/applicants/{own.id}/allocations/")
        assert response.status_code == 404

    def test_random_unscored_skips_own_application(self, client_logged_in, program, user):
        baker.make("grants.Applicant", program=program, email=user.email, name="Self")
        response = client_logged_in.get(f"/{program.slug}/applicants/random-unscored/")
        assert response.status_code == 302
        assert response.url.rstrip("/").endswith("/applicants")

    def test_same_name_applicant_still_visible(self, client_logged_in, program, user):
        """Regression: applicants with the same name as the reviewer must not be hidden."""
        user.first_name = "Ada"
        user.last_name = "Lovelace"
        user.save()
        namesake = baker.make(
            "grants.Applicant",
            program=program,
            email="different@example.com",
            name="Ada Lovelace",
        )
        response = client_logged_in.get(f"/{program.slug}/applicants/")
        assert namesake.name in response.content.decode()


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


class TestCreateProgramView:
    def test_requires_authentication(self, client, db):
        response = client.get("/programs/create/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_requires_staff_access(self, client, user):
        client.force_login(user)
        response = client.get("/programs/create/")
        assert response.status_code == 404

    def test_accessible_to_staff(self, client, user):
        user.is_staff = True
        user.save()
        client.force_login(user)
        response = client.get("/programs/create/")
        assert response.status_code == 200

    def test_creates_program_with_auto_slug(self, client, user):
        user.is_staff = True
        user.save()
        client.force_login(user)
        response = client.post(
            "/programs/create/",
            {"name": "New Conference"},
        )
        assert response.status_code == 302
        program = Program.objects.get(slug="new-conference")
        assert program.name == "New Conference"
        assert user in program.users.all()

    def test_auto_increments_duplicate_slug(self, client, user, program):
        user.is_staff = True
        user.save()
        client.force_login(user)
        response = client.post(
            "/programs/create/",
            {"name": program.name},
        )
        assert response.status_code == 302
        new_program = Program.objects.exclude(pk=program.pk).get()
        assert new_program.slug == f"{program.slug}-1"

    def test_join_code_defaults_to_slug(self, client, user):
        user.is_staff = True
        user.save()
        client.force_login(user)
        client.post(
            "/programs/create/",
            {"name": "Conference With Code"},
        )
        program = Program.objects.get(slug="conference-with-code")
        assert program.join_code == "conference-with-code"


class TestEditProgramView:
    def test_requires_authentication(self, client, program):
        response = client.get(f"/{program.slug}/edit/")
        assert response.status_code == 302
        assert "login" in response.url

    def test_requires_staff_access(self, client, program, user):
        program.users.add(user)
        client.force_login(user)
        response = client.get(f"/{program.slug}/edit/")
        assert response.status_code == 404

    def test_accessible_to_staff(self, client, program, user):
        user.is_staff = True
        user.save()
        program.users.add(user)
        client.force_login(user)
        response = client.get(f"/{program.slug}/edit/")
        assert response.status_code == 200

    def test_can_update_program_name(self, client, program, user):
        user.is_staff = True
        user.save()
        program.users.add(user)
        client.force_login(user)
        response = client.post(
            f"/{program.slug}/edit/",
            {"name": "Updated Name", "join_code": program.join_code or program.slug},
        )
        assert response.status_code == 302
        program.refresh_from_db()
        assert program.name == "Updated Name"

    def test_can_update_join_code(self, client, program, user):
        user.is_staff = True
        user.save()
        program.users.add(user)
        client.force_login(user)
        response = client.post(
            f"/{program.slug}/edit/",
            {"name": program.name, "join_code": "new-secret-code"},
        )
        assert response.status_code == 302
        program.refresh_from_db()
        assert program.join_code == "new-secret-code"
