from pyze.api import CredentialStore, Gigya

import getpass


def run(args):
    email = input('Enter your My Renault email address: ')
    password = getpass.getpass('Enter your password: ')

    creds = CredentialStore()

    g = Gigya(creds)
    print(g.login(email, password))
