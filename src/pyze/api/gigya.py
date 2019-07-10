import os
import requests


_ROOT_URL = 'https://accounts.eu1.gigya.com/'


class Gigya(object):
    def __init__(self):
        self._api_key = os.environ.get('GIGYA_API_KEY')

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
        return response
