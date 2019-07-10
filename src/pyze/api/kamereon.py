from .credentials import CredentialStore, requires_credentials
from .gigya import Gigya
from functools import lru_cache

import jwt
import os
import requests
import simplejson


_ROOT_URL = 'https://api-wired-prod-1-euw1.wrd-aws.com/commerce/v1'


class AccountException(Exception):
    def __init__(self, message):
        super().__init__(message)


class Kamereon(object):
    def __init__(self, credentials=CredentialStore(), country='GB'):
        self._api_key = os.environ.get('KAMEREON_API_KEY')

        if not self._api_key:
            raise Exception('KAMEREON_API_KEY environment variable not defined but required')

        self._credentials = credentials
        self._country = country
        self._gigya = Gigya(self._credentials)

    def _clear_all_caches(self):
        cached_funcs = [f for f in dir(self) if hasattr(f, 'cache_clear')]
        for func in cached_funcs:
            f.cache_clear()

    @requires_credentials('gigya', 'gigya-person-id')
    def get_account_id(self):
        if 'kamereon-account' in self._credentials:
            return self._credentials['kamereon-account']

        response = requests.get(
            '{}/persons/{}?country={}'.format(
                _ROOT_URL,
                self._credentials['gigya-person-id'],
                self._country
            ),
            headers={
                'apikey': self._api_key,
                'x-gigya-id_token': self._gigya.get_jwt_token()
            }
        )

        response.raise_for_status()
        response_body = response.json()

        accounts = response_body.get('accounts', [])
        if len(accounts) == 0:
            raise AccountException('No Kamereon accounts found!')
        if len(accounts) > 1:
            print("WARNING: Multiple Karmereon accounts found. Using the first.")

        account = accounts[0]
        self._clear_all_caches()
        self._credentials['kamereon-account'] = (account['accountId'], None)
        return account['accountId']

    @requires_credentials('gigya', 'gigya-person-id')
    def get_token(self):
        if 'kamereon' in self._credentials:
            return self._credentials['kamereon']

        response = requests.get(
            '{}/accounts/{}/kamereon/token?country={}'.format(
                _ROOT_URL,
                self.get_account_id(),
                self._country
            ),
            headers={
                'apikey': self._api_key,
                'x-gigya-id_token': self._gigya.get_jwt_token()
            }
        )

        response.raise_for_status()
        response_body = response.json()

        token = response_body.get('accessToken')
        if token:
            decoded = jwt.decode(token, options={'verify_signature': False, 'verify_aud': False})
            self._credentials['kamereon'] = (token, decoded['exp'])
            self._clear_all_caches()
            return token

        return False

    @lru_cache(maxsize=1)
    def get_vehicles(self):
        response = requests.get(
            '{}/accounts/{}/vehicles?country={}'.format(
                _ROOT_URL,
                self.get_account_id(),
                self._country
            ),
            headers={
                'apikey': self._api_key,
                'x-gigya-id_token': self._gigya.get_jwt_token(),
                'x-kamereon-authorization': self.get_token()
            }
        )

        response.raise_for_status()
        response_body = response.json()

        return response_body
