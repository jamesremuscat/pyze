from .credentials import requires_credentials, CredentialStore
from functools import lru_cache
from async_lru import alru_cache
from asgiref.sync import async_to_sync

import jwt
import logging
import os
import asyncio
import aiohttp


DEFAULT_ROOT_URL = 'https://accounts.eu1.gigya.com'
_log = logging.getLogger('pyze.api.gigya')


class Gigya(object):
    def __init__(
        self,
        api_key=None,
        credentials=None,
        root_url=DEFAULT_ROOT_URL,
        websession=None,
    ):
        self._credentials = credentials or CredentialStore()
        self._websession = websession
        self._root_url = root_url
        if api_key:
            self.set_api_key(api_key)

    def set_api_key(self, api_key):
        self._credentials.store('gigya-api-key', api_key, None)

    def login(self, user, password):
        return async_to_sync(self.login_async)(user, password)

    async def login_async(self, user, password, session=None):
        if 'gigya-api-key' not in self._credentials:
            raise RuntimeError('Gigya API key not specified. Call set_api_key or set GIGYA_API_KEY environment variable.')

        response_body = await self.http_request(
            None,
            'POST',
            self._root_url + '/accounts.login',
            data={
                'ApiKey': self._credentials['gigya-api-key'],
                'loginID': user,
                'password': password
            }
        )
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
        return async_to_sync(self.account_info_async)()

    @alru_cache(maxsize=1)
    @requires_credentials('gigya')
    async def account_info_async(self):
        response_body = await self.http_request(
            None,
            'POST',
            self._root_url + '/accounts.getAccountInfo',
            data={
                'oauth_token': self._credentials['gigya']
            }
        )
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
        return async_to_sync(self.get_jwt_token_async)()

    @requires_credentials('gigya')
    async def get_jwt_token_async(self):
        if 'gigya-token' in self._credentials:
            return self._credentials['gigya-token']

        response_body = await self.http_request(
            None,
            'POST',
            self._root_url + '/accounts.getJWT',
            data={
                'oauth_token': self._credentials['gigya'],
                'fields': 'data.personId,data.gigyaDataCenter',
                'expiration': 900
            }
        )
        token = response_body.get('id_token')

        if token:
            decoded = jwt.decode(token, options={'verify_signature': False})
            self._credentials['gigya-token'] = (token, decoded['exp'])
            return token

        raise RuntimeError('Unable to find Gigya JWT token in response: {}'.format(response.text))

    async def http_request(self, session, method, url, **kwargs):
        if session is None:
            session = self._websession
        if session is None:
            async with aiohttp.ClientSession() as websession:
                return await self.http_request(websession, method, url, **kwargs)

        _log.debug('Sending Gigya request to {} with data: {}'.format(url, kwargs.get('data', None)))
        async with await session.request(
            method,
            url,
            **kwargs
        ) as response:

            _log.debug('Received Gigya response: {}'.format(await response.text()))
            _log.debug('Received Gigya headers: {}'.format(response.headers))
            response.raise_for_status()
            response_body = await response.json(content_type='text/javascript')
            raise_gigya_errors(response_body)
            return response_body


def raise_gigya_errors(response_body):
    if response_body.get('errorCode', 0) > 0:
        raise RuntimeError(
            'Gigya returned error {}: {}'.format(
                response_body['errorCode'],
                response_body.get('errorDetails')
            )
        )
