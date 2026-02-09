from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User


class SalomViewTests(TestCase):
    """Salom (greeting) endpoint uchun testlar"""

    def setUp(self):
        self.client = Client()

    def test_salom_endpoint_returns_success(self):
        """Salom endpoint muvaffaqiyatli javob qaytarishi kerak"""
        response = self.client.get(reverse('salom'))
        self.assertEqual(response.status_code, 200)

    def test_salom_endpoint_returns_json(self):
        """Salom endpoint JSON formatida javob qaytarishi kerak"""
        response = self.client.get(reverse('salom'))
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_salom_endpoint_contains_greeting(self):
        """Salom endpoint javobida 'greeting' kaliti bo'lishi kerak"""
        response = self.client.get(reverse('salom'))
        data = response.json()
        self.assertIn('greeting', data)
        self.assertEqual(data['greeting'], 'Salom')

    def test_salom_endpoint_contains_message(self):
        """Salom endpoint javobida 'message' kaliti bo'lishi kerak"""
        response = self.client.get(reverse('salom'))
        data = response.json()
        self.assertIn('message', data)
        self.assertIn('Salom', data['message'])

    def test_salom_endpoint_personalized_for_authenticated_user(self):
        """Autentifikatsiya qilingan foydalanuvchi uchun shaxsiy xabar"""
        user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            first_name='Akobir'
        )
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('salom'))
        data = response.json()
        self.assertIn('Akobir', data['message'])
        self.assertIn("Cloudstore'ga xush kelibsiz", data['message'])

