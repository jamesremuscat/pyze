from .credentials import requires_credentials
from functools import lru_cache

import jwt
import os
import requests


_ROOT_URL = 'https://accounts.eu1.gigya.com/'


class Gigya(object):
    def __init__(self, credentials):
        self._api_key = os.environ.get('GIGYA_API_KEY')
        self._credentials = credentials
        self._session = requests.Session()

        if self._api_key is None:
            raise Exception('GIGYA_API_KEY environment variable not specified but required')

    def login(self, user, password):
        response = self._session.post(
            _ROOT_URL + 'accounts.login',
            data={
                'ApiKey': self._api_key,
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
            _ROOT_URL + 'accounts.getAccountInfo',
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
            _ROOT_URL + 'accounts.getJWT',
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

        return False
