from pyze.api import CredentialStore, Gigya

import getpass


def run(args):
    creds = CredentialStore()

    email = input('Enter your My Renault email address: ')
    password = getpass.getpass('Enter your password: ')

    g = Gigya(creds)
    print(g.login(email, password))
