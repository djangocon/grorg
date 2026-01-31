from __future__ import annotations

from model_bakery import baker

from grants.models import Applicant, Program, Question, Score


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

    def test_creates_program(self, client, user):
        user.is_staff = True
        user.save()
        client.force_login(user)
        response = client.post(
            "/programs/create/",
            {"name": "New Conference", "slug": "new-conference"},
        )
        assert response.status_code == 302
        program = Program.objects.get(slug="new-conference")
        assert program.name == "New Conference"
        assert user in program.users.all()

    def test_rejects_duplicate_slug(self, client, user, program):
        user.is_staff = True
        user.save()
        client.force_login(user)
        response = client.post(
            "/programs/create/",
            {"name": "Another Program", "slug": program.slug},
        )
        assert response.status_code == 200  # Form re-displayed with errors
        assert Program.objects.filter(slug=program.slug).count() == 1
