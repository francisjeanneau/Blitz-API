import json
import responses

from datetime import timedelta

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from django.utils import timezone
from django.urls import reverse

from blitz_api.factories import UserFactory, AdminFactory

from ..models import PaymentProfile

User = get_user_model()

SAMPLE_PAYSAFE_PROFILE = {
    "id": "19390257-a494-464e-95e6-6a24f1053289",
    "status": "ACTIVE",
    "merchantCustomerId": "mycustomer1",
    "locale": "en_US",
    "firstName": "John",
    "middleName": "James",
    "lastName": "Smith",
    "dateOfBirth": {
        "year": 1981,
        "month": 10,
        "day": 24
    },
    "ip": "192.0.126.111",
    "gender": "M",
    "nationality": "Canadian",
    "paymentToken": "P63dhGFvywNxhWd",
    "phone": "777-444-8888",
    "cellPhone": "777-555-8888",
    "email": "john.smith@email.com",
    "cards": [
        {
            "status": "ACTIVE",
            "id": "456",
            "cardBin": "453091",
            "lastDigits": "2345",
            "cardExpiry": {
                "year": 2019,
                "month": 12
            },
            "holderName": "John Smith",
            "nickName": "Personal Visa",
            "cardType": "VI",
            "paymentToken": "CIgbMO3P1j7HUiy",
            "defaultCardIndicator": True
        }
    ]
}

@override_settings(
    PAYSAFE={
        'ACCOUNT_NUMBER': "0123456789",
        'USER': "user",
        'PASSWORD': "password",
        'BASE_URL': "http://example.com/",
        'VAULT_URL': "customervault/v1/",
        'CARD_URL': "cardpayments/v1/"
    }
)
class PaymentProfileTests(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(PaymentProfileTests, cls).setUpClass()
        cls.maxDiff = None
        cls.client = APIClient()
        cls.user = UserFactory()
        cls.admin = AdminFactory()
        cls.payment_profile = PaymentProfile.objects.create(
            name="Test profile",
            owner=cls.user,
            external_api_id="123",
            external_api_url="https://example.com/customervault/v1/"
                             "profiles/",
        )
        cls.payment_profile_admin = PaymentProfile.objects.create(
            name="Test profile admin",
            owner=cls.admin,
            external_api_id="123",
            external_api_url="https://example.com/customervault/v1/"
                             "profiles/",
        )

    @responses.activate
    def test_list(self):
        """
        Ensure a user can only list his payment profile.
        """
        self.client.force_authenticate(user=self.user)

        responses.add(
            responses.GET,
            "http://example.com/customervault/v1/profiles/123?fields=cards",
            json=SAMPLE_PAYSAFE_PROFILE,
            status=200
        )

        response = self.client.get(
            reverse('paymentprofile-list'),
            format='json',
        )

        data = json.loads(response.content)

        content = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [{
                'external_data': {
                    'cards': [{
                        'cardBin': '453091',
                        'cardExpiry': {
                            'month': 12,
                            'year': 2019
                        },
                        'cardType': 'VI',
                        'defaultCardIndicator': True,
                        'holderName': 'John Smith',
                        'id': '456',
                        'lastDigits': '2345',
                        'nickName': 'Personal Visa',
                        'paymentToken': 'CIgbMO3P1j7HUiy',
                        'status': 'ACTIVE'
                    }],
                    'cellPhone': '777-555-8888',
                    'dateOfBirth': {
                        'day': 24,
                        'month': 10,
                        'year': 1981
                    },
                    'email': 'john.smith@email.com',
                    'firstName': 'John',
                    'gender': 'M',
                    'id': '19390257-a494-464e-95e6-6a24f1053289',
                    'ip': '192.0.126.111',
                    'lastName': 'Smith',
                    'locale': 'en_US',
                    'merchantCustomerId': 'mycustomer1',
                    'middleName': 'James',
                    'nationality': 'Canadian',
                    'paymentToken': 'P63dhGFvywNxhWd',
                    'phone': '777-444-8888',
                    'status': 'ACTIVE'
                },
                'id': 1,
                'name': 'Test profile',
                'owner': 'http://testserver/users/1'
            }]
        }

        self.assertEqual(data, content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @responses.activate
    def test_list_as_admin(self):
        """
        Ensure we can list all payment profiles as an admin.
        """
        self.client.force_authenticate(user=self.admin)

        responses.add(
            responses.GET,
            "http://example.com/customervault/v1/profiles/123?fields=cards",
            json=SAMPLE_PAYSAFE_PROFILE,
            status=200
        )

        response = self.client.get(
            reverse('paymentprofile-list'),
            format='json',
        )

        data = json.loads(response.content)

        content = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [{
                'external_data': {
                    'cards': [{
                        'cardBin': '453091',
                        'cardExpiry': {
                            'month': 12,
                            'year': 2019
                        },
                        'cardType': 'VI',
                        'defaultCardIndicator': True,
                        'holderName': 'John Smith',
                        'id': '456',
                        'lastDigits': '2345',
                        'nickName': 'Personal Visa',
                        'paymentToken': 'CIgbMO3P1j7HUiy',
                        'status': 'ACTIVE'
                    }],
                    'cellPhone': '777-555-8888',
                    'dateOfBirth': {
                        'day': 24,
                        'month': 10,
                        'year': 1981
                    },
                    'email': 'john.smith@email.com',
                    'firstName': 'John',
                    'gender': 'M',
                    'id': '19390257-a494-464e-95e6-6a24f1053289',
                    'ip': '192.0.126.111',
                    'lastName': 'Smith',
                    'locale': 'en_US',
                    'merchantCustomerId': 'mycustomer1',
                    'middleName': 'James',
                    'nationality': 'Canadian',
                    'paymentToken': 'P63dhGFvywNxhWd',
                    'phone': '777-444-8888',
                    'status': 'ACTIVE'
                },
                'id': 1,
                'name': 'Test profile',
                'owner': 'http://testserver/users/1'
            }, {
                'external_data': {
                    'cards': [{
                        'cardBin': '453091',
                        'cardExpiry': {
                            'month': 12,
                            'year': 2019
                        },
                        'cardType': 'VI',
                        'defaultCardIndicator': True,
                        'holderName': 'John Smith',
                        'id': '456',
                        'lastDigits': '2345',
                        'nickName': 'Personal Visa',
                        'paymentToken': 'CIgbMO3P1j7HUiy',
                        'status': 'ACTIVE'
                    }],
                    'cellPhone': '777-555-8888',
                    'dateOfBirth': {
                        'day': 24,
                        'month': 10,
                        'year': 1981
                    },
                    'email': 'john.smith@email.com',
                    'firstName': 'John',
                    'gender': 'M',
                    'id': '19390257-a494-464e-95e6-6a24f1053289',
                    'ip': '192.0.126.111',
                    'lastName': 'Smith',
                    'locale': 'en_US',
                    'merchantCustomerId': 'mycustomer1',
                    'middleName': 'James',
                    'nationality': 'Canadian',
                    'paymentToken': 'P63dhGFvywNxhWd',
                    'phone': '777-444-8888',
                    'status': 'ACTIVE'
                },
                'id': 2,
                'name': 'Test profile admin',
                'owner': 'http://testserver/users/2'
            }]
        }

        self.assertEqual(data, content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_unauthenticated(self):
        """
        Ensure that unauthenticated users can't list payment profiles.
        """
        response = self.client.get(
            reverse('paymentprofile-list'),
            format='json',
        )

        data = json.loads(response.content)

        content = {'detail': 'Authentication credentials were not provided.'}

        self.assertEqual(data, content)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @responses.activate
    def test_read(self):
        """
        Ensure a user can read his payment profile.
        """
        self.client.force_authenticate(user=self.user)

        responses.add(
            responses.GET,
            "http://example.com/customervault/v1/profiles/123?fields=cards",
            json=SAMPLE_PAYSAFE_PROFILE,
            status=200
        )

        response = self.client.get(
            reverse(
                'paymentprofile-detail',
                kwargs={'pk': 1},
            ),
        )

        data = json.loads(response.content)

        content = {
            'external_data': {
                'cards': [{
                    'cardBin': '453091',
                    'cardExpiry': {
                        'month': 12,
                        'year': 2019
                    },
                    'cardType': 'VI',
                    'defaultCardIndicator': True,
                    'holderName': 'John Smith',
                    'id': '456',
                    'lastDigits': '2345',
                    'nickName': 'Personal Visa',
                    'paymentToken': 'CIgbMO3P1j7HUiy',
                    'status': 'ACTIVE'
                }],
                'cellPhone': '777-555-8888',
                'dateOfBirth': {
                    'day': 24,
                    'month': 10,
                    'year': 1981
                },
                'email': 'john.smith@email.com',
                'firstName': 'John',
                'gender': 'M',
                'id': '19390257-a494-464e-95e6-6a24f1053289',
                'ip': '192.0.126.111',
                'lastName': 'Smith',
                'locale': 'en_US',
                'merchantCustomerId': 'mycustomer1',
                'middleName': 'James',
                'nationality': 'Canadian',
                'paymentToken': 'P63dhGFvywNxhWd',
                'phone': '777-444-8888',
                'status': 'ACTIVE'
            },
            'id': 1,
            'name': 'Test profile',
            'owner': 'http://testserver/users/1'
        }

        self.assertEqual(data, content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_read_without_permission(self):
        """
        Ensure a user can't read other users payment profile.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                'paymentprofile-detail',
                kwargs={'pk': 2},
            ),
        )

        data = json.loads(response.content)

        content = {'detail': "Not found."}

        self.assertEqual(data, content)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @responses.activate
    def test_read_admin(self):
        """
        Ensure that an admin can read other users payment profile.
        """
        self.client.force_authenticate(user=self.admin)

        responses.add(
            responses.GET,
            "http://example.com/customervault/v1/profiles/123?fields=cards",
            json=SAMPLE_PAYSAFE_PROFILE,
            status=200
        )

        response = self.client.get(
            reverse(
                'paymentprofile-detail',
                kwargs={'pk': 1},
            ),
        )

        data = json.loads(response.content)

        content = {
            'external_data': {
                'cards': [{
                    'cardBin': '453091',
                    'cardExpiry': {
                        'month': 12,
                        'year': 2019
                    },
                    'cardType': 'VI',
                    'defaultCardIndicator': True,
                    'holderName': 'John Smith',
                    'id': '456',
                    'lastDigits': '2345',
                    'nickName': 'Personal Visa',
                    'paymentToken': 'CIgbMO3P1j7HUiy',
                    'status': 'ACTIVE'
                }],
                'cellPhone': '777-555-8888',
                'dateOfBirth': {
                    'day': 24,
                    'month': 10,
                    'year': 1981
                },
                'email': 'john.smith@email.com',
                'firstName': 'John',
                'gender': 'M',
                'id': '19390257-a494-464e-95e6-6a24f1053289',
                'ip': '192.0.126.111',
                'lastName': 'Smith',
                'locale': 'en_US',
                'merchantCustomerId': 'mycustomer1',
                'middleName': 'James',
                'nationality': 'Canadian',
                'paymentToken': 'P63dhGFvywNxhWd',
                'phone': '777-444-8888',
                'status': 'ACTIVE'
            },
            'id': 1,
            'name': 'Test profile',
            'owner': 'http://testserver/users/1'
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_read_non_existent(self):
        """
        Ensure we get not found when asking for a payment profile that doesn't
        exist.
        """
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                'paymentprofile-detail',
                kwargs={'pk': 999},
            ),
        )

        content = {'detail': 'Not found.'}

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
