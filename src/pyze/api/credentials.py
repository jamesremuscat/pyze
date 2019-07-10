from collections import namedtuple

import os
import simplejson
import time


TOKEN_STORE = os.environ.get('PYZE_TOKEN_STORE', os.path.expanduser('~/.credentials/pyze.json'))


class MissingCredentialException(Exception):
    pass


def requires_credentials(*names):
    def _requires_credentials(func):
        def inner(*args, **kwargs):
            for name in names:
                if name not in CredentialStore():
                    raise MissingCredentialException()
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

    except:
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

        def __getitem__(self, name):
            if name in self._store:
                cred = self._store[name]
                if not cred.expiry or cred.expiry > time.time():
                    return cred.token
            raise KeyError(name)

        def __setitem__(self, name, value):
            return self.store(name, *value)

        def store(self, name, token, expiry):
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
            self._store = {}
            self._write()


Credential = namedtuple(
    'Credential',
    [
        'token',
        'expiry'
    ]
)
