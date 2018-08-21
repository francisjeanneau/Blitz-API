import requests
import random

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

PAYSAFE_EXCEPTIONS = [{
    'code': "5068",
    'message': _("Either you submitted a request that is missing a mandatory "
                 "field or the value of a field does not match the format "
                 "expected."),
    'fieldErrors': [{
        'field': 'card.paymentToken',
        'error': 'size must be between 10 and 80'
    }],
}]


def charge_payment(amount, payment_token, reference_number):
    """
    This method is used to charge an amount to a card represented by the
    payment token.
    This is tigthly coupled with Paysafe for now, but this should be made
    generic in the future to ease migrations to another payment patform.

    order:              Django Order model instance
    payment_profile:    Django PaymentProfile model instance
    """
    auth_url = '{0}{1}{2}{3}'.format(
        settings.PAYSAFE['BASE_URL'],
        settings.PAYSAFE['CARD_URL'],
        "accounts/" + settings.PAYSAFE['ACCOUNT_NUMBER'],
        "/auths/",
    )

    data = {
        "merchantRefNum": random.randint(0, 10000),
        # "merchantRefNum": reference_number,
        "amount": amount,
        "settleWithAuth": True,
        "card": {
            "paymentToken": payment_token,
        }
    }

    r = requests.post(
        auth_url,
        auth=(
            settings.PAYSAFE['USER'],
            settings.PAYSAFE['PASSWORD'],
        ),
        json=data,
    )
    r.raise_for_status()

    return r


def create_external_payment_profile(single_use_token, user):
    """
    This method is used to create a payment profile in external payment API.
    This is tigthly coupled with Paysafe for now, but this should be made
    generic in the future to ease migrations to another payment patform.

    payment_token:  Token that represents a payment card
    user:           Django User model instance
    """
    create_profile_url = '{0}{1}{2}'.format(
        settings.PAYSAFE['BASE_URL'],
        settings.PAYSAFE['VAULT_URL'],
        "profiles/",
    )

    data = {
        "merchantCustomerId": random.randint(0, 10000),
        # "merchantCustomerId": user.id,
        "locale": "en_US",
        "firstName": user.first_name,
        "lastName": user.last_name,
        "email": user.email,
        "phone": user.phone,
        "card": {
            "singleUseToken": single_use_token
        }
    }

    r = requests.post(
        create_profile_url,
        auth=(
            settings.PAYSAFE['USER'],
            settings.PAYSAFE['PASSWORD']
        ),
        json=data,
    )
    r.raise_for_status()

    return r


def get_external_payment_profile(profile_id):
    """
    This method is used to get a payment profile from an external payment API.
    This is tigthly coupled with Paysafe for now, but this should be made
    generic in the future to ease migrations to another payment patform.

    profile_id:   External profile ID
    """
    get_profile_url = '{0}{1}{2}{3}'.format(
        settings.PAYSAFE['BASE_URL'],
        settings.PAYSAFE['VAULT_URL'],
        "profiles/" + profile_id,
        "?fields=cards",
    )

    r = requests.get(
        get_profile_url,
        auth=(settings.PAYSAFE['USER'], settings.PAYSAFE['PASSWORD']),
    )
    r.raise_for_status()

    return r


def update_external_card(profile_id, card_id, single_use_token):
    """
    This method is used to update cards.
    This is tigthly coupled with Paysafe for now, but this should be made
    generic in the future to ease migrations to another payment patform.

    profile_id:         External profile ID
    card_id:            External card ID
    single_use_token:   Single use token representing the card instance
    """
    put_cards_url = '{0}{1}{2}{3}'.format(
        settings.PAYSAFE['BASE_URL'],
        settings.PAYSAFE['VAULT_URL'],
        "profiles/" + profile_id,
        "/cards/" + card_id,
    )

    data = {
        "singleUseToken": single_use_token
    }

    r = requests.put(
        put_cards_url,
        auth=(settings.PAYSAFE['USER'], settings.PAYSAFE['PASSWORD']),
        json=data,
    )
    r.raise_for_status()

    return r


def create_external_card(profile_id, single_use_token):
    """
    This method is used to add cards to a profile.
    This is tigthly coupled with Paysafe for now, but this should be made
    generic in the future to ease migrations to another payment patform.

    profile_id:         External profile ID
    single_use_token:   Single use token representing the card instance
    """
    post_cards_url = '{0}{1}{2}{3}'.format(
        settings.PAYSAFE['BASE_URL'],
        settings.PAYSAFE['VAULT_URL'],
        "profiles/" + profile_id,
        "/cards/",
    )

    data = {
        "singleUseToken": single_use_token
    }

    r = requests.post(
        post_cards_url,
        auth=(settings.PAYSAFE['USER'], settings.PAYSAFE['PASSWORD']),
        json=data,
    )
    r.raise_for_status()

    return r
