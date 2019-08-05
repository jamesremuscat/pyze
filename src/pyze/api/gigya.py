from .credentials import requires_credentials, CredentialStore
from functools import lru_cache

import jwt
import os
import requests


DEFAULT_ROOT_URL = 'https://accounts.eu1.gigya.com'


class Gigya(object):
    def __init__(
        self,
        api_key=None,
        credentials=None,
        root_url=DEFAULT_ROOT_URL,
    ):
        self._credentials = credentials or CredentialStore()
        self._session = requests.Session()
        self._root_url = root_url
        if api_key:
            self.set_api_key(api_key)

    def set_api_key(self, api_key):
        self._credentials.store('gigya-api-key', api_key, None)

    def login(self, user, password):
        if 'gigya-api-key' not in self._credentials:
            raise RuntimeError('Gigya API key not specified. Call set_api_key or set GIGYA_API_KEY environment variable.')

        response = self._session.post(
            self._root_url + '/accounts.login',
            data={
                'ApiKey': self._credentials['gigya-api-key'],
                'loginID': user,
                'password': password
            }
        )

        response.raise_for_status()

        response_body = response.json()

        token = response_body.get('sessionInfo', {}).get('cookieValue')

        if token:
            # Any stored credentials may be based on an old gigya login
            self._credentials.clear()
            self._credentials['gigya'] = (token, None)
            self.account_info.cache_clear()
            return response_body

        return False

    @lru_cache(maxsize=1)
    @requires_credentials('gigya')
    def account_info(self):
        response = self._session.post(
            self._root_url + '/accounts.getAccountInfo',
            {
                'oauth_token': self._credentials['gigya']
            }
        )

        response.raise_for_status()
        response_body = response.json()

        person_id = response_body.get('data', {}).get('personId')

        if person_id:
            self._credentials['gigya-person-id'] = (person_id, None)
            return response_body

        return False

    @requires_credentials('gigya')
    def get_jwt_token(self):

        if 'gigya-token' in self._credentials:
            return self._credentials['gigya-token']

        response = self._session.post(
            self._root_url + '/accounts.getJWT',
            {
                'oauth_token': self._credentials['gigya'],
                'fields': 'data.personId,data.gigyaDataCenter',
                'expiration': 900
            }
        )

        response.raise_for_status()
        response_body = response.json()

        token = response_body.get('id_token')

        if token:
            decoded = jwt.decode(token, options={'verify_signature': False})
            self._credentials['gigya-token'] = (token, decoded['exp'])
            return token

        raise RuntimeError('Unable to find Gigya JWT token in response: {}'.format(response.text))
