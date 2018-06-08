import json

from datetime import timedelta

from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from blitz_api.factories import UserFactory, AdminFactory
from location.models import Address, Country, StateProvince

from ..models import Workplace, Period

User = get_user_model()


class PeriodTests(APITestCase):

    @classmethod
    def setUpClass(cls):
        super(PeriodTests, cls).setUpClass()
        cls.client = APIClient()
        cls.user = UserFactory()
        cls.admin = AdminFactory()
        cls.random_country = Country.objects.create(
            name="Random_Country",
            iso_code="RC",
        )
        cls.random_state_province = StateProvince.objects.create(
            name="Random_State",
            iso_code="RS",
            country=cls.random_country,
        )
        cls.address = Address.objects.create(
            address_line1='random_address_1',
            postal_code='RAN_DOM',
            city='random_city',
            state_province=cls.random_state_province,
            country=cls.random_country,
        )
        cls.workplace = Workplace.objects.create(
            name="Blitz",
            seats=40,
            details="short_description",
            location=cls.address,
        )
        cls.period = Period.objects.create(
            name="random_period",
            workplace=cls.workplace,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(weeks=4),
            price=3,
            is_active=False,
        )
        cls.period = Period.objects.create(
            name="random_period_active",
            workplace=cls.workplace,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(weeks=4),
            price=3,
            is_active=True,
        )

    def test_create(self):
        """
        Ensure we can create a period if user has permission.
        """
        self.client.force_authenticate(user=self.admin)

        data = {
            'name': "random_period",
            'workplace': reverse('workplace-detail', args=[self.workplace.id]),
            'start_date': timezone.now() + timedelta(weeks=5),
            'end_date': timezone.now() + timedelta(weeks=10),
            'price': 3,
            'is_active': True,
        }

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {
            'id': 3,
            'end_date': data['end_date'].astimezone().isoformat(),
            'is_active': True,
            'name': 'random_period',
            'price': 3,
            'start_date': data['start_date'].astimezone().isoformat(),
            'url': 'http://testserver/periods/3',
            'workplace': 'http://testserver/workplaces/1'
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_without_permission(self):
        """
        Ensure we can't create a period if user has no permission.
        """
        self.client.force_authenticate(user=self.user)

        data = {
            'name': "random_period",
            'workplace': reverse('workplace-detail', args=[self.workplace.id]),
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(weeks=4),
            'price': 3,
            'is_active': True,
        }

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {
            'detail': 'You do not have permission to perform this action.'
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_overlapping(self):
        """
        Ensure we can't create overlapping period in the same workplace.
        """
        self.client.force_authenticate(user=self.admin)

        data = {
            'name': "random_period",
            'workplace': reverse('workplace-detail', args=[self.workplace.id]),
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(weeks=4),
            'price': 3,
            'is_active': True,
        }

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {
            'detail': [
                'An existing period overlaps with the provided start_date '
                'and end_date.'
            ]
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_start_end(self):
        """
        Ensure we can't create periods with start_date greater than end_date.
        """
        self.client.force_authenticate(user=self.admin)

        data = {
            'name': "random_period",
            'workplace': reverse('workplace-detail', args=[self.workplace.id]),
            'start_date': timezone.now(),
            'end_date': timezone.now() - timedelta(weeks=4),
            'price': 3,
            'is_active': True,
        }

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {
            'end_date': ['End date must be later than start_date.'],
            'start_date': ['End date must be earlier than end_date.']
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_non_existent_workplace(self):
        """
        Ensure we can't create a period with a non-existent workplace.
        """
        self.client.force_authenticate(user=self.admin)

        data = {
            'name': "random_period",
            'workplace': reverse('workplace-detail', args=[999]),
            'start_date': timezone.now(),
            'end_date': timezone.now() + timedelta(weeks=4),
            'price': 3,
            'is_active': True,
        }

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {'workplace': ['Invalid hyperlink - Object does not exist.']}

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_missing_field(self):
        """
        Ensure we can't create a period when required field are missing.
        """
        self.client.force_authenticate(user=self.admin)

        data = {}

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {
            'end_date': ['This field is required.'],
            'is_active': ['This field is required.'],
            'name': ['This field is required.'],
            'price': ['This field is required.'],
            'start_date': ['This field is required.'],
            'workplace': ['This field is required.']
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_blank_field(self):
        """
        Ensure we can't create a period when required field are blank.
        """
        self.client.force_authenticate(user=self.admin)

        data = {
            'name': None,
            'workplace': None,
            'start_date': None,
            'end_date': None,
            'price': None,
            'is_active': None,
        }

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {
            'name': ['This field may not be null.'],
            'start_date': ['This field may not be null.'],
            'end_date': ['This field may not be null.'],
            'price': ['This field may not be null.'],
            'is_active': ['This field may not be null.']
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invalid_field(self):
        """
        Ensure we can't create a timeslot when required field are invalid.
        """
        self.client.force_authenticate(user=self.admin)

        data = {
            'name': "",
            'workplace': "invalid",
            'start_date': "",
            'end_date': "",
            'price': "",
            'is_active': "",
        }

        response = self.client.post(
            reverse('period-list'),
            data,
            format='json',
        )

        content = {
            'end_date': [
                'Datetime has wrong format. Use one of these formats instead: '
                'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'
            ],
            'is_active': ['"" is not a valid boolean.'],
            'name': ['This field may not be blank.'],
            'price': ['A valid integer is required.'],
            'start_date': [
                'Datetime has wrong format. Use one of these formats instead: '
                'YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'
            ],
            'workplace': ['Invalid hyperlink - No URL match.']
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update(self):
        """
        Ensure we can update a period.
        """
        self.client.force_authenticate(user=self.admin)

        data = {
            'name': "new_period",
            'workplace': reverse('workplace-detail', args=[self.workplace.id]),
            'start_date': timezone.now() + timedelta(weeks=5),
            'end_date': timezone.now() + timedelta(weeks=10),
            'price': 3,
            'is_active': True,
        }

        response = self.client.put(
            reverse(
                'period-detail',
                kwargs={'pk': 1},
            ),
            data,
            format='json',
        )

        content = {
            'id': 1,
            'end_date': data['end_date'].astimezone().isoformat(),
            'is_active': True,
            'name': 'new_period',
            'price': 3,
            'start_date': data['start_date'].astimezone().isoformat(),
            'url': 'http://testserver/periods/1',
            'workplace': 'http://testserver/workplaces/1'
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete(self):
        """
        Ensure we can delete a period.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.delete(
            reverse(
                'period-detail',
                kwargs={'pk': 1},
            ),
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_list(self):
        """
        Ensure we can list active periods as an unauthenticated user if is
        active.
        """
        response = self.client.get(
            reverse('period-list'),
            format='json',
        )

        data = json.loads(response.content)

        content = {
            'count': 1,
            'next': None,
            'previous': None,
            'results': [{
                'id': 2,
                'end_date': data['results'][0]['end_date'],
                'is_active': True,
                'name': 'random_period_active',
                'price': 3,
                'start_date': data['results'][0]['start_date'],
                'url': 'http://testserver/periods/2',
                'workplace': 'http://testserver/workplaces/1'
            }]
        }

        self.assertEqual(data, content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_inactive(self):
        """
        Ensure we can list all periods as an admin user.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            reverse('period-list'),
            format='json',
        )

        data = json.loads(response.content)

        content = {
            'count': 2,
            'next': None,
            'previous': None,
            'results': [{
                'id': 1,
                'end_date': data['results'][0]['end_date'],
                'is_active': False,
                'name': 'random_period',
                'price': 3,
                'start_date': data['results'][0]['start_date'],
                'url': 'http://testserver/periods/1',
                'workplace': 'http://testserver/workplaces/1'
            }, {
                'id': 2,
                'end_date': data['results'][1]['end_date'],
                'is_active': True,
                'name': 'random_period_active',
                'price': 3,
                'start_date': data['results'][1]['start_date'],
                'url': 'http://testserver/periods/2',
                'workplace': 'http://testserver/workplaces/1'
            }]
        }

        self.assertEqual(data, content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_read(self):
        """
        Ensure we can read a period as an unauthenticated user if it is active.
        """

        response = self.client.get(
            reverse(
                'period-detail',
                kwargs={'pk': 2},
            ),
        )

        data = json.loads(response.content)

        content = {
            'id': 2,
            'end_date': data['end_date'],
            'is_active': True,
            'name': 'random_period_active',
            'price': 3,
            'start_date': data['start_date'],
            'url': 'http://testserver/periods/2',
            'workplace': 'http://testserver/workplaces/1'
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_read_inactive_non_admin(self):
        """
        Ensure we can't read a period as non_admin if it is inactive.
        """
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(
            reverse(
                'period-detail',
                kwargs={'pk': 1},
            ),
        )

        data = json.loads(response.content)

        content = {
            'id': 1,
            'end_date': data['end_date'],
            'is_active': False,
            'name': 'random_period',
            'price': 3,
            'start_date': data['start_date'],
            'url': 'http://testserver/periods/1',
            'workplace': 'http://testserver/workplaces/1'
        }

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_read_inactive(self):
        """
        Ensure we can read a period as admin if it is inactive.
        """

        response = self.client.get(
            reverse(
                'period-detail',
                kwargs={'pk': 1},
            ),
        )

        content = {'detail': 'Not found.'}

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_read_non_existent(self):
        """
        Ensure we get not found when asking for a period that doesn't exist.
        """

        response = self.client.get(
            reverse(
                'period-detail',
                kwargs={'pk': 999},
            ),
        )

        content = {'detail': 'Not found.'}

        self.assertEqual(json.loads(response.content), content)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)