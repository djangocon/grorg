from __future__ import annotations

import pytest
from model_bakery import baker


@pytest.fixture
def user(db):
    """Create a test user."""
    return baker.make("users.User", email="testuser@example.com")


@pytest.fixture
def other_user(db):
    """Create another test user for multi-user tests."""
    return baker.make("users.User", email="otheruser@example.com")


@pytest.fixture
def program(db, user):
    """Create a test program with the user as a member."""
    program = baker.make("grants.Program", name="Test Program", slug="test-program")
    program.users.add(user)
    return program


@pytest.fixture
def question(program):
    """Create a test question for the program."""
    return baker.make(
        "grants.Question",
        program=program,
        type="text",
        question="Why do you want this grant?",
        required=True,
        order=1,
    )


@pytest.fixture
def boolean_question(program):
    """Create a boolean question for the program."""
    return baker.make(
        "grants.Question",
        program=program,
        type="boolean",
        question="Are you a first-time attendee?",
        required=False,
        order=2,
    )


@pytest.fixture
def applicant(program):
    """Create a test applicant."""
    return baker.make(
        "grants.Applicant",
        program=program,
        name="Test Applicant",
        email="applicant@example.com",
    )


@pytest.fixture
def resource(program):
    """Create a test resource."""
    return baker.make(
        "grants.Resource",
        program=program,
        name="Travel Grant",
        type="money",
        amount=1000,
    )


@pytest.fixture
def score(applicant, user):
    """Create a test score."""
    return baker.make(
        "grants.Score",
        applicant=applicant,
        user=user,
        score=4.0,
        comment="Good application",
    )


@pytest.fixture
def client_logged_in(client, user):
    """Return a client with the user logged in."""
    client.force_login(user)
    return client
