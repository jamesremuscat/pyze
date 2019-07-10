from .credentials import requires_credential
from functools import lru_cache

import jwt
import os
import requests


_ROOT_URL = 'https://accounts.eu1.gigya.com/'


class Gigya(object):
    def __init__(self, credentials):
        self._api_key = os.environ.get('GIGYA_API_KEY')
        self._credentials = credentials

        if self._api_key is None:
            raise Exception('GIGYA_API_KEY environment variable not specified but required')

    def login(self, user, password):
        response = requests.post(
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
            self._credentials['gigya'] = (token, None)
            self.account_info.cache_clear()
            return response_body

        return False

    @lru_cache(maxsize=1)
    @requires_credential('gigya')
    def account_info(self):
        response = requests.post(
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

    @requires_credential('gigya')
    def get_jwt_token(self):
        response = requests.post(
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
            print(decoded)
            self._credentials['gigya-token'] = (token, decoded['exp'])
            return response_body

        return False
