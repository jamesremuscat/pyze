from .credentials import CredentialStore, requires_credentials
from .gigya import Gigya

import jwt
import os
import requests
import simplejson


_ROOT_URL = 'https://api-wired-prod-1-euw1.wrd-aws.com/commerce/v1/accounts/'


class Kamereon(object):
    def __init__(self, credentials=CredentialStore(), country='GB'):
        self._api_key = os.environ.get('KAMEREON_API_KEY')

        if not self._api_key:
            raise Exception('KAMEREON_API_KEY environment variable not defined but required')

        self._credentials = credentials
        self._country = country

    @requires_credentials('gigya', 'gigya-person-id')
    def get_token(self):
        if 'kamereon' in self._credentials:
            return self._credentials['kamereon']

        gigya = Gigya(self._credentials)

        response = requests.get(
            '{}{}/kamereon/token?country={}'.format(
                _ROOT_URL,
                self._credentials['gigya-person-id'],
                self._country
            ),
            headers={
                'apikey': self._api_key,
                'x-gigya-id_token': gigya.get_jwt_token()
            }
        )

        response.raise_for_status()
        response_body = response.json()

        token = response_body.get('accessToken')
        if token:
            decoded = jwt.decode(token, options={'verify_signature': False, 'verify_aud': False})
            self._credentials['kamereon'] = (token, decoded['exp'])

            return token

        return False
