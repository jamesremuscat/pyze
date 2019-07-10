from .credentials import CredentialStore, requires_credentials
from .gigya import Gigya
from .schedule import ChargeSchedule
from collections import namedtuple
from functools import lru_cache

import datetime
import dateutil.tz
import jwt
import os
import requests
import simplejson


_ROOT_URL = 'https://api-wired-prod-1-euw1.wrd-aws.com/commerce/v1'


class AccountException(Exception):
    def __init__(self, message):
        super().__init__(message)


class CachingAPIObject(object):
    def _clear_all_caches(self):
        cached_funcs = [f for f in dir(self) if hasattr(f, 'cache_clear')]
        for func in cached_funcs:
            f.cache_clear()


class Kamereon(CachingAPIObject):
    def __init__(self, credentials=CredentialStore(), country='GB'):
        self._api_key = os.environ.get('KAMEREON_API_KEY')

        if not self._api_key:
            raise Exception('KAMEREON_API_KEY environment variable not defined but required')

        self._credentials = credentials
        self._country = country
        self._gigya = Gigya(self._credentials)

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
                'x-kamereon-authorization': 'Bearer {}'.format(self.get_token())
            }
        )

        response.raise_for_status()
        response_body = response.json()

        return response_body


class Vehicle(object):
    def __init__(self, vin, kamereon=Kamereon()):
        self._vin = vin
        self._kamereon = kamereon

    def _request(self, method, endpoint, **kwargs):
        return requests.request(
            method,
            endpoint,
            headers={
                'Content-type': 'application/vnd.api+json',
                'apikey': self._kamereon._api_key,
                'x-gigya-id_token': self._kamereon._gigya.get_jwt_token(),
                'x-kamereon-authorization': 'Bearer {}'.format(self._kamereon.get_token())
            },
            **kwargs
        )

    def _get(self, endpoint):
        response = self._request(
            'GET',
            '{}/accounts/kmr/remote-services/car-adapter/v1/cars/{}/{}'.format(
                _ROOT_URL,
                self._vin,
                endpoint
            )
        )

        response.raise_for_status()
        return response.json()['data']['attributes']

    def _post(self, endpoint, data):
        response = self._request(
            'POST',
            '{}/accounts/kmr/remote-services/car-adapter/v1/cars/{}/{}'.format(
                _ROOT_URL,
                self._vin,
                endpoint
            ),
            json={
                'data': data
            }
        )

        response.raise_for_status()
        return response.json()

    def battery_status(self):
        return self._get('battery-status')

    def hvac_status(self):
        return self._get('hvac-status')

    def charge_mode(self):
        return self._get('charge-mode')

    def mileage(self):
        return self._get('cockpit')

    # Not (currently) implemented server-side
    def lock_status(self):
        return self._get('lock-status')

    # Not (currently) implemented server-side
    def location(self):
        return self._get('location')

    def charge_schedule(self):
        return ChargeSchedule(
            self._get('charge-schedule')
        )

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
