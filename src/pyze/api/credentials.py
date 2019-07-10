from collections import namedtuple

import time


def init_store():
    return {}


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
            self._store[name] = Credential(name, token, expiry)

        def __contains__(self, name):
            try:
                return self[name] is not None
            except KeyError:
                return False


Credential = namedtuple(
    'Credential',
    [
        'name',
        'token',
        'expiry'
    ]
)
