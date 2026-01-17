from django.test import TestCase


class SmokeTest(TestCase):
    def test_homepage_returns_200(self):
        response = self.client.get("/")
        assert response.status_code == 200
