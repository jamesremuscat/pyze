from collections import namedtuple

import os
import simplejson
import time


PERMANENT_KEYS = [
    'gigya-api-key',
    'kamereon-api-key'
]


class MissingCredentialException(Exception):
    pass


def requires_credentials(*names):
    def _requires_credentials(func):
        def inner(*args, **kwargs):
            credentials = None
            if args[0] and hasattr(args[0], '_credentials'):
                credentials = args[0]._credentials
            elif args[0] and hasattr(args[0], '_kamereon'):
                credentials = args[0]._kamereon._credentials
            for name in names:
                if name not in credentials:
                    raise MissingCredentialException(name)
            return func(*args, **kwargs)

        return inner
    return _requires_credentials


class CredentialStore(object):
    __instance = None

    def __new__(cls):
        if CredentialStore.__instance is None:
            default_store_location = os.environ.get('PYZE_TOKEN_STORE', os.path.expanduser('~/.credentials/pyze.json'))
            CredentialStore.__instance = FileCredentialStore(default_store_location)
        return CredentialStore.__instance


class BasicCredentialStore(object):
    def __init__(self):
        self._store = {}
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
        pass

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

    def requires(self, *names):
        for name in names:
            if name not in self._store:
                raise MissingCredentialException(name)


class FileCredentialStore(BasicCredentialStore):
    def __init__(self, store_location):
        self._store_location = store_location
        self._store = {}
        try:
            with open(self._store_location, 'r') as token_store:
                stored = simplejson.load(token_store)

                for key, value in stored.items():
                    self._store[key] = Credential(value['token'], value['expiry'])
        except Exception:
            pass
        self._add_api_keys_from_env()

    def _write(self):
        dirname = os.path.dirname(self._store_location)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)
        with open(self._store_location, 'w') as token_store:
            simplejson.dump(self._store, token_store)


Credential = namedtuple(
    'Credential',
    [
        'token',
        'expiry'
    ]
)
