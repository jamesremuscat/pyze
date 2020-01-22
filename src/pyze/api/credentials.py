from collections import namedtuple

import os
import simplejson
import time


TOKEN_STORE = os.environ.get('PYZE_TOKEN_STORE', os.path.expanduser('~/.credentials/pyze.json'))

PERMANENT_KEYS = [
    'gigya-api-key',
    'kamereon-api-key'
]


class MissingCredentialException(Exception):
    pass


def requires_credentials(*names):
    def _requires_credentials(func):
        def inner(*args, **kwargs):
            for name in names:
                if name not in CredentialStore():
                    raise MissingCredentialException(name)
            return func(*args, **kwargs)

        return inner
    return _requires_credentials


def init_store():
    new_store = {}
    try:
        with open(TOKEN_STORE, 'r') as token_store:
            stored = simplejson.load(token_store)

            for key, value in stored.items():
                new_store[key] = Credential(value['token'], value['expiry'])
    except Exception:
        pass

    return new_store


class CredentialStore(object):
    __instance = None

    def __new__(cls):
        if CredentialStore.__instance is None:
            CredentialStore.__instance = CredentialStore._CredentialStore()
        return CredentialStore.__instance

    class _CredentialStore(object):
        def __init__(self):
            self._store = init_store()
            self._add_api_keys_from_env()

        def __getitem__(self, name):
            if name in self._store:
                cred = self._store[name]
                if not cred.expiry or cred.expiry > time.time():
                    return cred.token
            raise KeyError(name)

        def __setitem__(self, name, value):
            return self.store(name, *value)

        def store(self, name, token, expiry):
            if not isinstance(name, str):
                raise RuntimeError('Credential name must be a string')
            if not isinstance(token, str):
                raise RuntimeError('Credential value must be a string')
            self._store[name] = Credential(token, expiry)
            self._write()

        def _write(self):
            dirname = os.path.dirname(TOKEN_STORE)
            if not os.path.isdir(dirname):
                os.makedirs(dirname)
            with open(TOKEN_STORE, 'w') as token_store:
                simplejson.dump(self._store, token_store)

        def __contains__(self, name):
            try:
                return self[name] is not None
            except KeyError:
                return False

        def clear(self):
            for k in list(self._store.keys()):
                if k not in PERMANENT_KEYS:
                    del self._store[k]
            self._write()

        def _add_api_keys_from_env(self):
            if 'GIGYA_API_KEY' in os.environ:
                self.store('gigya-api-key', os.environ['GIGYA_API_KEY'], None)

            if 'KAMEREON_API_KEY' in os.environ:
                self.store('kamereon-api-key', os.environ['KAMEREON_API_KEY'], None)


Credential = namedtuple(
    'Credential',
    [
        'token',
        'expiry'
    ]
)
