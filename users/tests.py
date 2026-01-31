from __future__ import annotations

import pytest
from model_bakery import baker

from users.models import User


class TestUserModel:
    def test_create_user(self, db):
        user = baker.make("users.User", email="test@example.com")
        assert user.email == "test@example.com"
        assert user.is_active

    def test_create_user_with_password(self, db):
        user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        assert user.email == "test@example.com"
        assert user.check_password("testpass123")
        assert user.is_active
        assert not user.is_staff

    def test_create_superuser(self, db):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass123",
        )
        assert user.email == "admin@example.com"
        assert user.is_active
        assert user.is_staff
        assert user.is_superuser

    def test_user_str_returns_name_when_set(self, db):
        user = baker.make("users.User", name="John Doe", email="john@example.com")
        assert str(user) == "John Doe"

    def test_user_str_returns_email_when_no_name(self, db):
        user = baker.make("users.User", name="", email="display@example.com")
        assert str(user) == "display@example.com"

    def test_user_has_email_as_username_field(self):
        assert User.USERNAME_FIELD == "email"

    def test_get_full_name_returns_name(self, db):
        user = baker.make("users.User", name="Jane Smith")
        assert user.get_full_name() == "Jane Smith"

    def test_get_short_name_returns_name(self, db):
        user = baker.make("users.User", name="Jane Smith")
        assert user.get_short_name() == "Jane Smith"


@pytest.mark.django_db
def test_user_email_is_unique():
    baker.make("users.User", email="unique@example.com")
    with pytest.raises(Exception):
        baker.make("users.User", email="unique@example.com")
