from django.test import TestCase

from users.models import User


class UserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )
        assert user.email == "test@example.com"
        assert user.is_active
        assert not user.is_staff
