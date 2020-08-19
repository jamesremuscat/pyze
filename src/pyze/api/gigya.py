from .credentials import requires_credentials, CredentialStore
from functools import lru_cache

import jwt
import logging
import os
import requests


DEFAULT_ROOT_URL = 'https://accounts.eu1.gigya.com'
_log = logging.getLogger('pyze.api.gigya')


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
        _log.debug('Received Gigya login response: {}'.format(response_body))
        raise_gigya_errors(response_body)

        token = response_body.get('sessionInfo', {}).get('cookieValue')

        if token:
            # Any stored credentials may be based on an old gigya login
            self._credentials.clear()
            self._credentials['gigya'] = (token, None)
            self.account_info.cache_clear()
            return response_body
        else:
            raise RuntimeError(
                'Unable to find Gigya token from login response! Response included keys {}'.format(
                    ', '.join(response_body.keys())
                )
            )

    @lru_cache(maxsize=1)
    @requires_credentials('gigya')
    def account_info(self):
        if 'gigya-api-key' not in self._credentials:
            raise RuntimeError('Gigya API key not specified. Call set_api_key or set GIGYA_API_KEY environment variable.')

        response = self._session.post(
            self._root_url + '/accounts.getAccountInfo',
            {
                'ApiKey': self._credentials['gigya-api-key'],
                'login_token': self._credentials['gigya']
            }
        )

        response.raise_for_status()
        response_body = response.json()
        _log.debug('Received Gigya accountInfo response: {}'.format(response_body))
        raise_gigya_errors(response_body)

        person_id = response_body.get('data', {}).get('personId')

        if person_id:
            self._credentials['gigya-person-id'] = (person_id, None)
            return response_body

        raise RuntimeError(
            'Unable to find Gigya person ID from account info! Response contained keys {}'.format(
                ', '.join(response_body.keys())
            )
        )

    @requires_credentials('gigya')
    def get_jwt_token(self):

        if 'gigya-token' in self._credentials:
            return self._credentials['gigya-token']

        if 'gigya-api-key' not in self._credentials:
            raise RuntimeError('Gigya API key not specified. Call set_api_key or set GIGYA_API_KEY environment variable.')

        response = self._session.post(
            self._root_url + '/accounts.getJWT',
            {
                'ApiKey': self._credentials['gigya-api-key'],
                'login_token': self._credentials['gigya'],
                'fields': 'data.personId,data.gigyaDataCenter',
                'expiration': 900
            }
        )

        response.raise_for_status()
        response_body = response.json()
        _log.debug('Received Gigya getJWT response: {}'.format(response_body))
        raise_gigya_errors(response_body)

        token = response_body.get('id_token')

        if token:
            decoded = jwt.decode(token, options={'verify_signature': False})
            self._credentials['gigya-token'] = (token, decoded['exp'])
            return token

        raise RuntimeError('Unable to find Gigya JWT token in response: {}'.format(response.text))


def raise_gigya_errors(response_body):
    if response_body.get('errorCode', 0) > 0:
        raise RuntimeError(
            'Gigya returned error {}: {}'.format(
                response_body['errorCode'],
                response_body.get('errorDetails')
            )
        )
