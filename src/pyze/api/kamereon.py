from .credentials import DefaultCredentialStore
from .gigya import Gigya, GigyaAsync
from .schedule import ChargeSchedules, ChargeMode
from collections import namedtuple
from enum import Enum
from functools import lru_cache
from async_lru import alru_cache

import datetime
import dateutil.tz
import itertools
import jwt
import logging
import os
import requests
import asyncio
import aiohttp
import simplejson


DEFAULT_ROOT_URL = 'https://api-wired-prod-1-euw1.wrd-aws.com'
_log = logging.getLogger('pyze.api.kamereon')


class AccountException(Exception):
    def __init__(self, message):
        super().__init__(message)


class CachingAPIObject(object):
    def _clear_all_caches(self):
        cached_funcs = [f for f in dir(self) if hasattr(f, 'cache_clear')]
        for func in cached_funcs:
            f.cache_clear()


class Kamereon(CachingAPIObject):
    def __init__(
        self,
        api_key=None,
        credentials=None,
        gigya=None,
        country='GB',
        root_url=DEFAULT_ROOT_URL
    ):

        self._root_url = root_url
        self._credentials = credentials or DefaultCredentialStore()
        self._country = country
        self._gigya = gigya or Gigya(credentials=self._credentials)
        self._session = requests.Session()
        if api_key:
            self.set_api_key(api_key)

    @staticmethod
    def print_multiple_account_warning(accounts):
        print("WARNING: Multiple Kamereon accounts found:")
        for acc in accounts:
            print('- {}'.format(acc['accountId']))
        print('Using the first of these. If that\'s not correct (perhaps you can\'t see your vehicle)')
        print('or to silence this message, run `pyze set-account` or set the KAMEREON_ACCOUNT_ID')
        print('environment variable to the account you want to use i.e.')
        print('    KAMEREON_ACCOUNT_ID=abcdef123456789 pyze ...')
        print('API users may instead call Kamereon#set_account_id().')
        print('This setting will persist until you next log in.')

    def set_api_key(self, api_key):
        self._credentials.store('kamereon-api-key', api_key, None)

    def get_account_id(self):
        if 'KAMEREON_ACCOUNT_ID' in os.environ:
            self.set_account_id(os.environ['KAMEREON_ACCOUNT_ID'])
        if 'kamereon-account' in self._credentials:
            return self._credentials['kamereon-account']

        accounts = self.get_accounts()

        if len(accounts) == 0:
            raise AccountException('No Kamereon accounts found!')
        if len(accounts) > 1:
            Kamereon.print_multiple_account_warning(accounts)

        account = accounts[0]
        self._clear_all_caches()
        self._credentials['kamereon-account'] = (account['accountId'], None)
        return account['accountId']

    def get_accounts(self):
        self._credentials.requires('gigya', 'gigya-person-id', 'kamereon-api-key')
        response = self._session.get(
            '{}/commerce/v1/persons/{}?country={}'.format(
                self._root_url,
                self._credentials['gigya-person-id'],
                self._country
            ),
            headers={
                'apikey': self._credentials['kamereon-api-key'],
                'x-gigya-id_token': self._gigya.get_jwt_token()
            }
        )

        response.raise_for_status()
        response_body = response.json()
        _log.debug('Received Kamereon accounts response: {}'.format(response_body))

        return response_body.get('accounts', [])

    def set_account_id(self, account_id):
        self._credentials['kamereon-account'] = (account_id, None)

    def get_token(self):
        self._credentials.requires('gigya', 'gigya-person-id', 'kamereon-api-key')
        if 'kamereon' in self._credentials:
            return self._credentials['kamereon']

        response = self._session.get(
            '{}/commerce/v1/accounts/{}/kamereon/token?country={}'.format(
                self._root_url,
                self.get_account_id(),
                self._country
            ),
            headers={
                'apikey': self._credentials['kamereon-api-key'],
                'x-gigya-id_token': self._gigya.get_jwt_token()
            }
        )

        response.raise_for_status()
        response_body = response.json()
        _log.debug('Received Kamereon token response: {}'.format(response_body))

        token = response_body.get('accessToken')
        if token:
            decoded = jwt.decode(
                token,
                options={
                    'verify_signature': False,
                    'verify_aud': False,
                    'verify_nbf': False
                }
            )
            self._credentials['kamereon'] = (token, decoded['exp'])
            self._clear_all_caches()
            return token
        else:
            raise AccountException(
                'Unable to obtain a Kamereon access token! Response included keys {}'.format(
                    ', '.join(response_body.keys())
                )
            )

    @lru_cache(maxsize=1)
    def get_vehicles(self):
        self._credentials.requires('kamereon-api-key')
        response = self._session.get(
            '{}/commerce/v1/accounts/{}/vehicles?country={}'.format(
                self._root_url,
                self.get_account_id(),
                self._country
            ),
            headers={
                'apikey': self._credentials['kamereon-api-key'],
                'x-gigya-id_token': self._gigya.get_jwt_token(),
                'x-kamereon-authorization': 'Bearer {}'.format(self.get_token())
            }
        )

        response.raise_for_status()
        response_body = response.json()
        _log.debug('Received Kamereon vehicles response: {}'.format(response_body))

        return response_body


class KamereonAsync(CachingAPIObject):
    def __init__(
        self,
        api_key=None,
        credentials=None,
        gigya=None,
        country='GB',
        root_url=DEFAULT_ROOT_URL,
        websession=None,
    ):

        self._root_url = root_url
        self._credentials = credentials or DefaultCredentialStore()
        self._country = country
        self._websession = websession
        self._websession_autoclear = False
        if websession is None:
            self._websession_autoclear = True
            self._websession = aiohttp.ClientSession()
        self._gigya = gigya or GigyaAsync(credentials=self._credentials, websession=self._websession)
        if api_key:
            self.set_api_key(api_key)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *excinfo):
        if self._websession_autoclear:
            await self._websession.close()

    @staticmethod
    def print_multiple_account_warning(accounts):
        print("WARNING: Multiple Kamereon accounts found:")
        for acc in accounts:
            print('- {}'.format(acc['accountId']))
        print('Using the first of these. If that\'s not correct (perhaps you can\'t see your vehicle)')
        print('or to silence this message, run `pyze set-account` or set the KAMEREON_ACCOUNT_ID')
        print('environment variable to the account you want to use i.e.')
        print('    KAMEREON_ACCOUNT_ID=abcdef123456789 pyze ...')
        print('API users may instead call Kamereon#set_account_id().')
        print('This setting will persist until you next log in.')

    def set_api_key(self, api_key):
        self._credentials.store('kamereon-api-key', api_key, None)

    async def get_account_id(self):
        if 'KAMEREON_ACCOUNT_ID' in os.environ:
            self.set_account_id(os.environ['KAMEREON_ACCOUNT_ID'])
        if 'kamereon-account' in self._credentials:
            return self._credentials['kamereon-account']

        accounts = await self.get_accounts()

        if len(accounts) == 0:
            raise AccountException('No Kamereon accounts found!')
        if len(accounts) > 1:
            Kamereon.print_multiple_account_warning(accounts)

        account = accounts[0]
        self._clear_all_caches()
        self._credentials['kamereon-account'] = (account['accountId'], None)
        return account['accountId']

    async def get_accounts(self):
        self._credentials.requires('gigya', 'gigya-person-id', 'kamereon-api-key')
        async with self._websession.get(
            '{}/commerce/v1/persons/{}?country={}'.format(
                self._root_url,
                self._credentials['gigya-person-id'],
                self._country
            ),
            headers={
                'apikey': self._credentials['kamereon-api-key'],
                'x-gigya-id_token': await self._gigya.get_jwt_token()
            }
        ) as response:

            response.raise_for_status()
            response_body = await response.json()
            _log.debug('Received Kamereon accounts response: {}'.format(response_body))

            return response_body.get('accounts', [])

    def set_account_id(self, account_id):
        self._credentials['kamereon-account'] = (account_id, None)

    async def get_token(self):
        self._credentials.requires('gigya', 'gigya-person-id', 'kamereon-api-key')
        if 'kamereon' in self._credentials:
            return self._credentials['kamereon']

        async with self._websession.get(
            '{}/commerce/v1/accounts/{}/kamereon/token?country={}'.format(
                self._root_url,
                await self.get_account_id(),
                self._country
            ),
            headers={
                'apikey': self._credentials['kamereon-api-key'],
                'x-gigya-id_token': await self._gigya.get_jwt_token()
            }
        ) as response:

            response.raise_for_status()
            response_body = await response.json()
            _log.debug('Received Kamereon token response: {}'.format(response_body))

            token = response_body.get('accessToken')
            if token:
                decoded = jwt.decode(
                    token,
                    options={
                        'verify_signature': False,
                        'verify_aud': False,
                        'verify_nbf': False
                    }
                )
                self._credentials['kamereon'] = (token, decoded['exp'])
                self._clear_all_caches()
                return token
            else:
                raise AccountException(
                    'Unable to obtain a Kamereon access token! Response included keys {}'.format(
                        ', '.join(response_body.keys())
                    )
                )

    @alru_cache(maxsize=1)
    async def get_vehicles(self):
        self._credentials.requires('kamereon-api-key')
        async with self._websession.get(
            '{}/commerce/v1/accounts/{}/vehicles?country={}'.format(
                self._root_url,
                await self.get_account_id(),
                self._country
            ),
            headers={
                'apikey': self._credentials['kamereon-api-key'],
                'x-gigya-id_token': await self._gigya.get_jwt_token(),
                'x-kamereon-authorization': 'Bearer {}'.format(await self.get_token())
            }
        ) as response:

            response.raise_for_status()
            response_body = await response.json()
            _log.debug('Received Kamereon vehicles response: {}'.format(response_body))

            return response_body


class Vehicle(object):
    def __init__(self, vin, kamereon=None):
        self._vin = vin
        self._kamereon = kamereon or Kamereon()
        self._root_url = self._kamereon._root_url

    def _request(self, method, endpoint, **kwargs):
        self._kamereon._credentials.requires('kamereon-api-key')
        return self._kamereon._session.request(
            method,
            endpoint,
            headers={
                'Content-type': 'application/vnd.api+json',
                'apikey': self._kamereon._credentials['kamereon-api-key'],
                'x-gigya-id_token': self._kamereon._gigya.get_jwt_token(),
                'x-kamereon-authorization': 'Bearer {}'.format(self._kamereon.get_token())
            },
            params={
                'country': self._kamereon._country
            },
            **kwargs
        )

    def _get(self, endpoint, version=1):
        response = self._request(
            'GET',
            '{}/commerce/v1/accounts/{}/kamereon/kca/car-adapter/v{}/cars/{}/{}'.format(
                self._root_url,
                self._kamereon.get_account_id(),
                version,
                self._vin,
                endpoint
            )
        )

        _log.debug('Received Kamereon vehicle response: {}'.format(response.text))
        _log.debug('Response headers: {}'.format(response.headers))
        response.raise_for_status()
        json = response.json()
        return json['data']['attributes']

    def _post(self, endpoint, data, version=1):
        _log.debug('POSTing with data: {}'.format(data))
        response = self._request(
            'POST',
            '{}/commerce/v1/accounts/{}/kamereon/kca/car-adapter/v{}/cars/{}/{}'.format(
                self._root_url,
                self._kamereon.get_account_id(),
                version,
                self._vin,
                endpoint
            ),
            json={
                'data': data
            }
        )

        _log.debug('Received Kamereon vehicle response: {}'.format(response.text))
        _log.debug('Response headers: {}'.format(response.headers))
        response.raise_for_status()
        json = response.json()
        return json

    def battery_status(self):
        return self._get('battery-status', 2)

    def location(self):
        return self._get('location')

    def hvac_status(self):
        return self._get('hvac-status')

    def charge_mode(self):
        raw_mode = self._get('charge-mode')['chargeMode']
        if hasattr(ChargeMode, raw_mode):
            return getattr(ChargeMode, raw_mode)
        else:
            return raw_mode

    def mileage(self):
        return self._get('cockpit', 2)

    # Not (currently) implemented server-side
    def lock_status(self):
        return self._get('lock-status')

    # Not implemented server-side for most vehicles
    def location(self):
        return self._get('location')

    def charge_schedules(self):
        return ChargeSchedules(
            self._get('charging-settings')
        )

    def notification_settings(self):
        return self._get('notification-settings')

    def charge_history(self, start, end):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))

        return self._get(
            'charges?start={}&end={}'.format(
                start.strftime('%Y%m%d'),
                end.strftime('%Y%m%d')
            )
        ).get('charges', [])

    def charge_statistics(self, start, end, period='month'):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))
        if period not in PERIOD_FORMATS.keys():
            raise RuntimeError('`period` should be one of `month`, `day`')

        return self._get(
            'charge-history?type={}&start={}&end={}'.format(
                period,
                start.strftime(PERIOD_FORMATS[period]),
                end.strftime(PERIOD_FORMATS[period])
            )
        )['chargeSummaries']

    def hvac_history(self, start, end):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))

        return self._get(
            'hvac-sessions?start={}&end={}'.format(
                start.strftime('%Y%m%d'),
                end.strftime('%Y%m%d')
            )
        ).get('hvacSessions', [])

    def hvac_statistics(self, start, end, period='month'):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))
        if period not in PERIOD_FORMATS.keys():
            raise RuntimeError('`period` should be one of `month`, `day`')

        return self._get(
            'hvac-history?type={}&start={}&end={}'.format(
                period,
                start.strftime(PERIOD_FORMATS[period]),
                end.strftime(PERIOD_FORMATS[period])
            )
        )['hvacSessionsSummaries']

    # Actions

    def ac_start(self, when=None, temperature=21):

        attrs = {
            'action': 'start',
            'targetTemperature': temperature
        }

        if when:

            if not isinstance(when, datetime.datetime):
                raise RuntimeError('`when` should be an instance of datetime.datetime, not {}'.format(when.__class__))

            attrs['startDateTime'] = when.astimezone(
                dateutil.tz.tzutc()
            ).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        return self._post(
            'actions/hvac-start',
            {
                'type': 'HvacStart',
                'attributes': attrs
            }
        )

    def cancel_ac(self):
        return self._post(
            'actions/hvac-start',
            {
                'type': 'HvacStart',
                'attributes': {
                    'action': 'cancel'
                }
            }
        )

    def set_charge_schedules(self, schedules):
        if not isinstance(schedules, ChargeSchedules):
            raise RuntimeError('Expected schedule to be instance of ChargeSchedules, but got {} instead'.format(schedule.__class__))
        schedules.validate()

        data = {
            'type': 'ChargeSchedule',
            'attributes': schedules
        }

        return self._post(
            'actions/charge-schedule',
            simplejson.loads(simplejson.dumps(data, for_json=True)),
            version=2
        )

    def set_charge_mode(self, charge_mode):
        if not isinstance(charge_mode, ChargeMode):
            raise RuntimeError('Expected charge_mode to be instance of ChargeMode, but got {} instead'.format(charge_mode.__class__))

        data = {
            'type': 'ChargeMode',
            'attributes': {
                'action': charge_mode.name
            }
        }

        return self._post(
            'actions/charge-mode',
            data
        )

    def charge_start(self):
        return self._post(
            'actions/charging-start',
            {
                'type': 'ChargingStart',
                'attributes': {
                    'action': 'start'
                }
            }
        )


class VehicleAsync(object):
    def __init__(self, vin, kamereon=None):
        self._vin = vin
        self._kamereon = kamereon or KamereonAsync()
        self._root_url = self._kamereon._root_url

    async def _request(self, method, url, **kwargs):
        self._kamereon._credentials.requires('kamereon-api-key')
        async with await self._kamereon._websession.request(
            method,
            url,
            headers={
                'Content-type': 'application/vnd.api+json',
                'apikey': self._kamereon._credentials['kamereon-api-key'],
                'x-gigya-id_token': await self._kamereon._gigya.get_jwt_token(),
                'x-kamereon-authorization': 'Bearer {}'.format(await self._kamereon.get_token())
            },
            params={
                'country': self._kamereon._country
            },
            **kwargs
        ) as response:

            _log.debug('Received Kamereon vehicle response: {}'.format(await response.text()))
            _log.debug('Response headers: {}'.format(response.headers))
            response.raise_for_status()
            return await response.json()

    async def _get(self, endpoint, version=1):
        _log.debug('GETing from {}'.format(endpoint))
        json = await self._request(
            'GET',
            '{}/commerce/v1/accounts/{}/kamereon/kca/car-adapter/v{}/cars/{}/{}'.format(
                self._root_url,
                await self._kamereon.get_account_id(),
                version,
                self._vin,
                endpoint
            )
        )
        return json['data']['attributes']

    async def _post(self, endpoint, data, version=1):
        _log.debug('POSTing to {} with data: {}'.format(endpoint, data))
        json = await self._request(
            'POST',
            '{}/commerce/v1/accounts/{}/kamereon/kca/car-adapter/v{}/cars/{}/{}'.format(
                self._root_url,
                await self._kamereon.get_account_id(),
                version,
                self._vin,
                endpoint
            ),
            json={
                'data': data
            }
        )
        return json

    async def battery_status(self):
        return await self._get('battery-status', 2)

    async def location(self):
        return await self._get('location')

    async def hvac_status(self):
        return await self._get('hvac-status')

    async def charge_mode(self):
        raw_mode = (await self._get('charge-mode'))['chargeMode']
        if hasattr(ChargeMode, raw_mode):
            return getattr(ChargeMode, raw_mode)
        else:
            return raw_mode

    async def mileage(self):
        return await self._get('cockpit', 2)

    # Not (currently) implemented server-side
    async def lock_status(self):
        return await self._get('lock-status')

    # Not implemented server-side for most vehicles
    async def location(self):
        return await self._get('location')

    async def charge_schedules(self):
        return ChargeSchedules(
            await self._get('charging-settings')
        )

    async def notification_settings(self):
        return await self._get('notification-settings')

    async def charge_history(self, start, end):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))

        return await self._get(
            'charges?start={}&end={}'.format(
                start.strftime('%Y%m%d'),
                end.strftime('%Y%m%d')
            )
        ).get('charges', [])

    async def charge_statistics(self, start, end, period='month'):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))
        if period not in PERIOD_FORMATS.keys():
            raise RuntimeError('`period` should be one of `month`, `day`')

        return await self._get(
            'charge-history?type={}&start={}&end={}'.format(
                period,
                start.strftime(PERIOD_FORMATS[period]),
                end.strftime(PERIOD_FORMATS[period])
            )
        )['chargeSummaries']

    async def hvac_history(self, start, end):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))

        return await self._get(
            'hvac-sessions?start={}&end={}'.format(
                start.strftime('%Y%m%d'),
                end.strftime('%Y%m%d')
            )
        ).get('hvacSessions', [])

    async def hvac_statistics(self, start, end, period='month'):
        if not isinstance(start, datetime.datetime):
            raise RuntimeError('`start` should be an instance of datetime.datetime, not {}'.format(start.__class__))
        if not isinstance(end, datetime.datetime):
            raise RuntimeError('`end` should be an instance of datetime.datetime, not {}'.format(end.__class__))
        if period not in PERIOD_FORMATS.keys():
            raise RuntimeError('`period` should be one of `month`, `day`')

        return await self._get(
            'hvac-history?type={}&start={}&end={}'.format(
                period,
                start.strftime(PERIOD_FORMATS[period]),
                end.strftime(PERIOD_FORMATS[period])
            )
        )['hvacSessionsSummaries']

    # Actions

    async def ac_start(self, when=None, temperature=21):

        attrs = {
            'action': 'start',
            'targetTemperature': temperature
        }

        if when:

            if not isinstance(when, datetime.datetime):
                raise RuntimeError('`when` should be an instance of datetime.datetime, not {}'.format(when.__class__))

            attrs['startDateTime'] = when.astimezone(
                dateutil.tz.tzutc()
            ).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )

        return await self._post(
            'actions/hvac-start',
            {
                'type': 'HvacStart',
                'attributes': attrs
            }
        )

    async def cancel_ac(self):
        return await self._post(
            'actions/hvac-start',
            {
                'type': 'HvacStart',
                'attributes': {
                    'action': 'cancel'
                }
            }
        )

    async def set_charge_schedules(self, schedules):
        if not isinstance(schedules, ChargeSchedules):
            raise RuntimeError('Expected schedule to be instance of ChargeSchedules, but got {} instead'.format(schedule.__class__))
        schedules.validate()

        data = {
            'type': 'ChargeSchedule',
            'attributes': schedules
        }

        return await self._post(
            'actions/charge-schedule',
            simplejson.loads(simplejson.dumps(data, for_json=True)),
            version=2
        )

    async def set_charge_mode(self, charge_mode):
        if not isinstance(charge_mode, ChargeMode):
            raise RuntimeError('Expected charge_mode to be instance of ChargeMode, but got {} instead'.format(charge_mode.__class__))

        data = {
            'type': 'ChargeMode',
            'attributes': {
                'action': charge_mode.name
            }
        }

        return await self._post(
            'actions/charge-mode',
            data
        )

    async def charge_start(self):
        return await self._post(
            'actions/charging-start',
            {
                'type': 'ChargingStart',
                'attributes': {
                    'action': 'start'
                }
            }
        )

# Serious metaprogramming follows:
# https://www.notinventedhere.org/articles/python/how-to-use-strings-as-name-aliases-in-python-enums.html


_CHARGE_STATES = {
    0.0: ['Not charging', 'NOT_IN_CHARGE'],
    0.1: ['Waiting for planned charge', 'WAITING_FOR_PLANNED_CHARGE'],
    0.2: ['Charge ended', 'CHARGE_ENDED'],
    0.3: ['Waiting for current charge', 'WAITING_FOR_CURRENT_CHARGE'],
    0.4: ['Energy flap opened', 'ENERGY_FLAP_OPENED'],
    1.0: ['Charging', 'CHARGE_IN_PROGRESS'],
    # This next is more accurately "not charging" (<= ZE40) or "error" (ZE50).
    # But I don't want to include 'error' in the output text because people will
    # think that it's an error in Pyze when their ZE40 isn't plugged in...
    -1.0: ['Not charging or plugged in', 'CHARGE_ERROR'],
    -1.1: ['Not available', 'NOT_AVAILABLE']
}

ChargeState = Enum(
    value='ChargeState',
    names=itertools.chain.from_iterable(
        itertools.product(v, [k]) for k, v in _CHARGE_STATES.items()
    )
)

_PLUG_STATES = {
    0: ['Unplugged', 'UNPLUGGED'],
    1: ['Plugged in', 'PLUGGED'],
    -1: ['Plug error', 'PLUG_ERROR'],
    -2147483648: ['Not available', 'NOT_AVAILABLE']
}

PlugState = Enum(
    value='PlugState',
    names=itertools.chain.from_iterable(
        itertools.product(v, [k]) for k, v in _PLUG_STATES.items()
    )
)


PERIOD_FORMATS = {
    'day': '%Y%m%d',
    'month': '%Y%m'
}
