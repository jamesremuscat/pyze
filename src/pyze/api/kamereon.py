from .credentials import CredentialStore, requires_credentials
from .gigya import Gigya
from .schedule import ChargeSchedule, ChargeMode
from collections import namedtuple
from functools import lru_cache

import datetime
import dateutil.tz
import jwt
import os
import requests
import json


DEFAULT_ROOT_URL = 'https://api-wired-prod-1-euw1.wrd-aws.com'


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
        self._credentials = credentials or CredentialStore()
        self._country = country
        self._gigya = gigya or Gigya(credentials=self._credentials)
        self._session = requests.Session()
        if api_key:
            self.set_api_key(api_key)

    def set_api_key(self, api_key):
        self._credentials.store('kamereon-api-key', api_key, None)

    @requires_credentials('gigya', 'gigya-person-id', 'kamereon-api-key')
    def get_account_id(self):
        if 'kamereon-account' in self._credentials:
            return self._credentials['kamereon-account']

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

        accounts = response_body.get('accounts', [])
        if len(accounts) == 0:
            raise AccountException('No Kamereon accounts found!')
        if len(accounts) > 1:
            print("WARNING: Multiple Kamereon accounts found. Using the first.")

        account = accounts[0]
        self._clear_all_caches()
        self._credentials['kamereon-account'] = (account['accountId'], None)
        return account['accountId']

    @requires_credentials('gigya', 'gigya-person-id', 'kamereon-api-key')
    def get_token(self):
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

        token = response_body.get('accessToken')
        if token:
            decoded = jwt.decode(token, options={'verify_signature': False, 'verify_aud': False})
            self._credentials['kamereon'] = (token, decoded['exp'])
            self._clear_all_caches()
            return token

        return False

    @lru_cache(maxsize=1)
    @requires_credentials('kamereon-api-key')
    def get_vehicles(self):
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

        return response_body


class Vehicle(object):
    def __init__(self, vin, kamereon=None):
        self._vin = vin
        self._kamereon = kamereon or Kamereon()
        self._root_url = self._kamereon._root_url

    @requires_credentials('kamereon-api-key')
    def _request(self, method, endpoint, **kwargs):
        return self._kamereon._session.request(
            method,
            endpoint,
            headers={
                'Content-type': 'application/vnd.api+json',
                'apikey': self._kamereon._credentials['kamereon-api-key'],
                'x-gigya-id_token': self._kamereon._gigya.get_jwt_token(),
                'x-kamereon-authorization': 'Bearer {}'.format(self._kamereon.get_token())
            },
            **kwargs
        )

    def _get(self, endpoint):
        response = self._request(
            'GET',
            '{}/commerce/v1/accounts/kmr/remote-services/car-adapter/v1/cars/{}/{}'.format(
                self._root_url,
                self._vin,
                endpoint
            )
        )

        response.raise_for_status()
        return response.json()['data']['attributes']

    def _post(self, endpoint, data):
        response = self._request(
            'POST',
            '{}/commerce/v1/accounts/kmr/remote-services/car-adapter/v1/cars/{}/{}'.format(
                self._root_url,
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
        raw_mode = self._get('charge-mode')['chargeMode']
        if hasattr(ChargeMode, raw_mode):
            return getattr(ChargeMode, raw_mode)
        else:
            return raw_mode

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

    def set_charge_schedule(self, schedule):
        if not isinstance(schedule, ChargeSchedule):
            raise RuntimeError('Expected schedule to be instance of ChargeSchedule, but got {} instead'.format(schedule.__class__))
        schedule.validate()

        data = {
            'type': 'ChargeSchedule',
            'attributes': schedule
        }

        return self._post(
            'actions/charge-schedule',
            json.loads(json.dumps(data, for_json=True))
        )

    def set_charge_mode(self, charge_mode):
        if not isinstance(charge_mode, ChargeMode):
            raise RuntimeError('Expceted charge_mode to be instance of ChargeMode, but got {} instead'.format(charge_mode.__class__))

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


PERIOD_FORMATS = {
    'day': '%Y%m%d',
    'month': '%Y%m'
}
