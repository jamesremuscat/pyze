from pyze.api import CredentialStore, Gigya

import getpass


help_text = 'Log in to your MY Renault account.'


def run(args):
    creds = CredentialStore()

    email = input('Enter your My Renault email address: ')
    password = getpass.getpass('Enter your password: ')

    g = Gigya(creds)
    if g.login(email, password):
        g.account_info()
        print('Logged in successfully.')
    else:
        print('Failed to log in!')
